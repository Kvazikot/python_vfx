QT       += core gui widgets
QT += opengl concurrent

TARGET = livegpu
TEMPLATE = app
SOURCES += main.cpp \
    cellularautomatas.cpp \
    livewidget.cpp \
    quadsprite.cpp

HEADERS += \
    cellularautomatas.h \
    quadsprite.h \
    livewidget.h

RESOURCES += \
        shaders.qrc \
        textures.qrc

DISTFILES += \
    cube.png
