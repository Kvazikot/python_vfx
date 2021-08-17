#include <QDebug>
#include <QApplication>
#define _USE_MATH_DEFINES
#include <math.h>
#include "livewidget.h"

int main(int argc, char *argv[])
{
    //qApp->addLibraryPath("./plugins");
	QApplication a(argc, argv);    
    LiveWidget w;
    w.show();
    //qDebug() << calculate_pi();
	return a.exec();
}
