#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QtMqtt/QMqttClient>
#include <openssl/ssl.h>
#include <openssl/err.h>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QPlainTextEdit>

QT_BEGIN_NAMESPACE
namespace Ui {
class MainWindow;
}
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void on_pushButton_clicked();    // Upload button
    void on_pushButton_2_clicked();  // Download button
    void on_pushButton_3_clicked();  // Save button

private:
    // Setup functions
    void setupMqttClient();
    void setupInitialUI();
    void setupMessageHandler();

    // MQTT operations
    void subscribeToTopics(const QStringList &topics);
    bool publishMessage(const QString &topic, const QByteArray &message);

    // File operations
    bool saveJsonToFile(const QByteArray &jsonData, const QString &filePath);

    // Member variables
    Ui::MainWindow *ui;
    QMqttClient *mqttClient;  // MQTT client as class member instead of global
};

#endif // MAINWINDOW_H
