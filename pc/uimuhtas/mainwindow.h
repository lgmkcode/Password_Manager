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

// Global MQTT istemci tanımı
extern QMqttClient* globalMqttClient;

QT_BEGIN_NAMESPACE
namespace Ui {
class MainWindow;
}
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

    // Yeni eklenen subscribeToTopic fonksiyonu prototipi
    void subscribeToTopic(const QString &topic);

private slots:
    void on_pushButton_clicked();

    void on_pushButton_2_clicked();

    void on_pushButton_3_clicked();

private:
    Ui::MainWindow *ui;
};

#endif // MAINWINDOW_H
