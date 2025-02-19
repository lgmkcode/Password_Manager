#include "mainwindow.h"
#include "./ui_mainwindow.h"
#include <QtMqtt/QMqttClient>
#include <QJsonDocument>
#include <QJsonParseError>
#include <QFile>
#include <QDebug>

namespace {
// Configuration constants
const QString MQTT_HOST = "192.168.207.93";
const int MQTT_PORT = 9999;
const QString JSON_FILE_PATH = "/home/lgmk/Desktop/Password_Project_Mqtt/pc/password_pc.json";

// MQTT Topics
const QString TOPIC_PC_TO_RPI_FLAG = "pc-to-rpi-flag";
const QString TOPIC_PC_TO_RPI_DATA = "pc-to-rpi-data";
const QString TOPIC_RPI_TO_PC_DATA = "rpi-to-pc-data";

// UI Messages
const QString MSG_WELCOME = "Password manager sistemine hoş geldiniz\n"
                            "Şifrelerinizi indirmek için download password butonuna basın ve yönergeleri takip edin.";
const QString MSG_UPLOAD_SUCCESS = "Şifreleriniz database'e gönderilmiştir";
const QString MSG_DOWNLOAD_PROMPT = "Kartınızı okutun ardından pin kodunuzu giriniz.";
const QString MSG_SAVE_SUCCESS = "Şifreleriniz kaydedildi\n"
                                 "Upload password butonuna basarak şifrelerinizi database'e gönderebilirsiniz.";
}

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
    , mqttClient(new QMqttClient(this))
{
    ui->setupUi(this);
    setupMqttClient();
    setupInitialUI();
}

MainWindow::~MainWindow()
{
    delete ui;
}

void MainWindow::setupMqttClient()
{
    mqttClient->setHostname(MQTT_HOST);
    mqttClient->setPort(MQTT_PORT);

    // MQTT bağlantısı kurulduktan sonra topic'lere abone ol
    connect(mqttClient, &QMqttClient::connected, this, [this]{
        qDebug() << "MQTT Client connected.";
        qDebug() << "MQTT Client State:" << mqttClient->state();

        // Bağlantı kurulduktan sonra topic'lere abone ol
        subscribeToTopics({
            TOPIC_PC_TO_RPI_FLAG,
            TOPIC_PC_TO_RPI_DATA,
            TOPIC_RPI_TO_PC_DATA
        });
    });

    connect(mqttClient, &QMqttClient::disconnected, this, []{
        qDebug() << "MQTT Client disconnected.";
    });

    mqttClient->connectToHost();
}

void MainWindow::setupInitialUI()
{
    ui->plainTextEdit->setPlainText(MSG_WELCOME);
}

void MainWindow::subscribeToTopics(const QStringList &topics)
{
    for (const QString &topic : topics) {
        auto subscription = mqttClient->subscribe(topic);
        if (subscription) {
            qDebug() << "Successfully subscribed to:" << topic;
        } else {
            qDebug() << "Failed to subscribe to:" << topic;
        }
    }
}

bool MainWindow::publishMessage(const QString &topic, const QByteArray &message)
{
    if (mqttClient->state() != QMqttClient::Connected) {
        qDebug() << "MQTT Client not connected!";
        return false;
    }

    if (mqttClient->publish(topic, message) == -1) {
        qDebug() << "Failed to publish message to topic:" << topic;
        return false;
    }

    qDebug() << "Successfully published message to topic:" << topic;
    return true;
}

bool MainWindow::saveJsonToFile(const QByteArray &jsonData, const QString &filePath)
{
    QJsonParseError parseError;
    QJsonDocument jsonDoc = QJsonDocument::fromJson(jsonData, &parseError);

    if (parseError.error != QJsonParseError::NoError) {
        qDebug() << "JSON parse error:" << parseError.errorString();
        return false;
    }

    QFile file(filePath);
    if (!file.open(QIODevice::WriteOnly)) {
        qDebug() << "Failed to open file for writing:" << filePath;
        return false;
    }

    file.write(jsonDoc.toJson(QJsonDocument::Indented));
    file.close();
    return true;
}

void MainWindow::on_pushButton_clicked()  // Upload button
{
    QFile file(JSON_FILE_PATH);
    if (!file.open(QIODevice::ReadOnly)) {
        qDebug() << "Failed to open JSON file for reading";
        return;
    }

    QByteArray jsonData = file.readAll();
    file.close();

    if (publishMessage(TOPIC_PC_TO_RPI_DATA, jsonData)) {
        publishMessage(TOPIC_PC_TO_RPI_FLAG, "send_start_flag");
        ui->plainTextEdit->setPlainText(MSG_UPLOAD_SUCCESS);
    }
}

void MainWindow::on_pushButton_2_clicked()  // Download button
{
    ui->plainTextEdit->setPlainText(MSG_DOWNLOAD_PROMPT);

    if (publishMessage(TOPIC_PC_TO_RPI_FLAG, "pull-start-flag")) {
        setupMessageHandler();
    }
}

void MainWindow::setupMessageHandler()
{
    connect(mqttClient, &QMqttClient::messageReceived, this,
            [this](const QByteArray &message, const QMqttTopicName &topicName) {
                qDebug() << "Received message on topic:" << topicName.name();
                qDebug() << "Message content:" << message;

                if (topicName.name() == TOPIC_RPI_TO_PC_DATA) {
                    if (saveJsonToFile(message, JSON_FILE_PATH)) {
                        QJsonDocument jsonDoc = QJsonDocument::fromJson(message);
                        ui->plainTextEdit->setPlainText(QString(jsonDoc.toJson(QJsonDocument::Indented)));
                        qDebug() << "Successfully processed and displayed message";
                    }
                    // Disconnect only after successful processing
                    disconnect(mqttClient, &QMqttClient::messageReceived, this, nullptr);
                }
            });
}

void MainWindow::on_pushButton_3_clicked()  // Save button
{
    QString text = ui->plainTextEdit->toPlainText();
    if (saveJsonToFile(text.toUtf8(), JSON_FILE_PATH)) {
        ui->plainTextEdit->setPlainText(MSG_SAVE_SUCCESS);
    }
}
