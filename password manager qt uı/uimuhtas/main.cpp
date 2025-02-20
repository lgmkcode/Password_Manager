#include "mainwindow.h"

#include <QApplication>
#include <QtMqtt/QMqttClient>
#include <QDebug>
#include <openssl/ssl.h>
#include <openssl/err.h>

#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QPlainTextEdit>


int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    MainWindow w;
    w.show();
    return a.exec();
}
