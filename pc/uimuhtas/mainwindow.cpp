#include "mainwindow.h"
#include "./ui_mainwindow.h"
#include <QtMqtt/QMqttClient>

// Global MQTT istemcinin tanımı
QMqttClient* globalMqttClient = nullptr;

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);

    // MQTT istemcisini oluşturma ve başlatma
    globalMqttClient = new QMqttClient(this);
    globalMqttClient->setHostname("192.168.250.93");
    globalMqttClient->setPort(9999);

    // Durum değişikliklerini kontrol etmek için sinyal-slot bağlantıları
    connect(globalMqttClient, &QMqttClient::connected, this, []() {
        qDebug() << "MQTT Client connected.";
    });
    connect(globalMqttClient, &QMqttClient::disconnected, this, []() {
        qDebug() << "MQTT Client disconnected.";
    });

    // MQTT istemcisine bağlan
    globalMqttClient->connectToHost();

    // Abone olma işlemini constructor'da yapalım
    subscribeToTopic("pc-to-rpi-flag");
    subscribeToTopic("pc-to-rpi-data");
    subscribeToTopic("rpi-to-pc-data");
    //subscribeToTopic("rpi-to-pc-flag");

    ui->plainTextEdit->setPlainText("Password manager sistemine hoş geldiniz\nŞifrelerinizi indirmek için download password butonuna basın ve yönergeleri takip edin.");
}

MainWindow::~MainWindow()
{
    delete ui;
}


void MainWindow::subscribeToTopic(const QString &topic)
{
    if (globalMqttClient)
    {
        globalMqttClient->subscribe(topic);
    }
}


void MainWindow::on_pushButton_clicked()
{  //////////////// upload button ////////////////////

    ////////////////////////////// SEND START FLAG ////////////////////////////////

    // JSON dosyasını okuma
    QFile file("/home/lgmk/Desktop/Password_Project_Mqtt/pc/password_pc.json");
    if (!file.open(QIODevice::ReadOnly)) {
        qDebug() << "JSON dosyası açılamadı";
        return;
    }
    QByteArray jsonData = file.readAll();
    file.close();

    // Bağlantı sağlandığında mesaj gönderme
    if (globalMqttClient->state() == QMqttClient::Connected) {
        QString topic = "pc-to-rpi-data";
        if (globalMqttClient->publish(topic, jsonData) == -1) {
            qDebug() << "Mesaj gönderilemedi!";
        } else {
            qDebug() << "Mesaj gönderildi";
            if (globalMqttClient->state() == QMqttClient::Connected) {
                QString topic = "pc-to-rpi-flag";
                if (globalMqttClient->publish(topic, "send_start_flag") == -1) {
                    qDebug() << "Flag gönderilemedi!";
                } else {
                    qDebug() << "Flag gönderildi";
                }
            } else {
                connect(globalMqttClient, &QMqttClient::connected, this, [=]() {
                    qDebug() << "MQTT Client connected - Sending message";
                    QString topic = "pc-to-rpi-flag";
                    if (globalMqttClient->publish(topic, "send_start_flag") == -1) {
                        qDebug() << "Flag gönderilemedi!";
                    } else {
                        qDebug() << "Flag gönderildi";
                    }
                });
            }
        }
    } else {
        connect(globalMqttClient, &QMqttClient::connected, this, [=]() {
            qDebug() << "MQTT Client connected - Sending message";
            QString topic = "pc-to-rpi-data";
            if (globalMqttClient->publish(topic, jsonData) == -1) {
                qDebug() << "Mesaj gönderilemedi!";
            } else {
                qDebug() << "Mesaj gönderildi";
                if (globalMqttClient->state() == QMqttClient::Connected) {
                    QString topic = "pc-to-rpi-flag";
                    if (globalMqttClient->publish(topic, "send_start_flag") == -1) {
                        qDebug() << "Flag gönderilemedi!";
                    } else {
                        qDebug() << "Flag gönderildi";
                    }
                } else {
                    connect(globalMqttClient, &QMqttClient::connected, this, [=]() {
                        qDebug() << "MQTT Client connected - Sending message";
                        QString topic = "pc-to-rpi-flag";
                        if (globalMqttClient->publish(topic, "send_start_flag") == -1) {
                            qDebug() << "Flag gönderilemedi!";
                        } else {
                            qDebug() << "Flag gönderildi";
                        }
                    });
                }
            }
        });
    }
    ui->plainTextEdit->setPlainText("Şifreleriniz database'e gönderilmiştir");
}


void MainWindow::on_pushButton_2_clicked()
{   //////////// download button ///////////////
    ui->plainTextEdit->setPlainText("Kartınızı okutun ardından pin kodunuzu giriniz.");
    ////////////////////////////// PULL START FLAG ////////////////////////////////

    // Bağlantı sağlandığında mesaj gönderme
    if (globalMqttClient->state() == QMqttClient::Connected) {
        QString topic = "pc-to-rpi-flag";
        if (globalMqttClient->publish(topic, "pull-start-flag") == -1) {
            qDebug() << "Flag gönderilemedi!";
        } else {
            qDebug() << "Flag gönderildi";
        }
    } else {
        connect(globalMqttClient, &QMqttClient::connected, this, [=]() {
            qDebug() << "MQTT Client connected - Sending message";
            QString topic = "pc-to-rpi-flag";
            if (globalMqttClient->publish(topic, "pull-start-flag") == -1) {
                qDebug() << "Flag gönderilemedi!";
            } else {
                qDebug() << "Flag gönderildi";
            }
        });
    }

    ////////////////////////////// RECEIVE DATA FROM rpi-to-pc-data ////////////////////////////////

    connect(globalMqttClient, &QMqttClient::messageReceived, this, [=](const QByteArray &message, const QMqttTopicName &topicName) {
        qDebug() << "Im here";
        qDebug() << "Topic: " << topicName.name();
        QString topic = topicName.name();
        if (topic == "rpi-to-pc-data") {
                QJsonParseError parseError;
                QJsonDocument jsonDoc = QJsonDocument::fromJson(message, &parseError);

                if (parseError.error != QJsonParseError::NoError)
                {
                    qDebug() << "JSON parse error:" << parseError.errorString();
                    return;
                }

                QFile jsonFile("/home/lgmk/Desktop/Password_Project_Mqtt/pc/password_pc.json");
                if (!jsonFile.open(QIODevice::WriteOnly | QIODevice::Text))
                {
                    qDebug() << "Failed to open JSON file for writing.";
                    return;
                }

                jsonFile.write(jsonDoc.toJson(QJsonDocument::Indented));
                jsonFile.flush();
                jsonFile.close();

                qDebug() << "JSON file updated successfully.";

                ui->plainTextEdit->setPlainText(QString(jsonDoc.toJson(QJsonDocument::Indented)));

                disconnect(globalMqttClient, &QMqttClient::messageReceived, this, nullptr);
        }
    });

    // "rpi-to-pc-data" konusuna abone oluyoruz
    subscribeToTopic("rpi-to-pc-data");
}

void MainWindow::on_pushButton_3_clicked()
{ ////////////////// save button//////////////////////

    // QPlainTextEdit'teki JSON formatındaki metni al
    QString text = ui->plainTextEdit->toPlainText();

    // JSON doğrulaması yap
    QJsonParseError parseError;
    QJsonDocument jsonDoc = QJsonDocument::fromJson(text.toUtf8(), &parseError);

    if (parseError.error != QJsonParseError::NoError) {
        // JSON formatı hatalıysa hata mesajı yazdır
        qWarning() << "Geçersiz JSON formatı:" << parseError.errorString();
        return;
    }

    // Dosyayı yazma modunda aç
    QFile file("/home/lgmk/Desktop/Password_Project_Mqtt/pc/password_pc.json");
    if (!file.open(QIODevice::WriteOnly)) {
        qWarning("JSON dosyası açılamadı!");
        return;
    }

    // JSON dökümanını dosyaya yaz
    file.write(jsonDoc.toJson());
    file.close();
    ui->plainTextEdit->setPlainText("Şifreleriniz kaydedildi\nUpload password butonuna basarak şifrelerinizi database'e gönderebilirsiniz.");
    qDebug() << "JSON dosyaya başarıyla kaydedildi.";
}
