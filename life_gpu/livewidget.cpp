#include "livewidget.h"
#include "cellularautomatas.h"
#include <QDebug>
#include <QMouseEvent>
#include <QOpenGLFramebufferObject>
#include <QOpenGLTexture>
#include <math.h>

GLuint FramebufferName = 0;


QOpenGLTexture* texture1;

LiveWidget::LiveWidget(QWidget *parent) :
    angularSpeed(0)
{
    framebuffer = 0;
    n_frame = 0;
    RES_X = 320;
    RES_Y = 240;
    zDist = 1;
    bNeedReinitTexture = 0;
    setGeometry(100, 100, RES_X, RES_Y);
    startTimer(50);
}

LiveWidget::~LiveWidget()
{

}

//! [0]
void LiveWidget::mousePressEvent(QMouseEvent *e)
{
    // Save mouse press position
    mousePressPosition = QVector2D(e->localPos());
}

void LiveWidget::wheelEvent(QWheelEvent *e)
{
    qDebug() << e->angleDelta();
    // Reset projection
    projectionScreen.setToIdentity();
    if( e->angleDelta().y() > 0 )
        zDist-=0.1;
    else
        zDist+=0.1;
   const qreal zNear = 0.0, zFar = 1000.0;
    projectionScreen.ortho(-1,1,-1,1,zNear,zFar);
    projectionScreen.scale(zDist);

}

void LiveWidget::mouseMoveEvent(QMouseEvent *e)
{
    QVector2D diff = QVector2D(e->localPos()) - mousePressPosition;
    qDebug() << diff;
    projectionScreen.setToIdentity();
    const qreal zNear = 0.0, zFar = 1000.0;
    projectionScreen.ortho(-1,1,-1,1,zNear,zFar);
    projectionScreen.translate(-(float)diff.x()/100,-(float)diff.y()/100,0);
    projectionScreen.scale(zDist);


}

void LiveWidget::mouseReleaseEvent(QMouseEvent *e)
{
    // Mouse release position - mouse press position
    QVector2D diff = QVector2D(e->localPos()) - mousePressPosition;

    //projectionScreen.translate(diff);

    // Rotation axis is perpendicular to the mouse position difference
    // vector
    QVector3D n = QVector3D(diff.y(), diff.x(), 0.0).normalized();

    // Accelerate angular speed relative to the length of the mouse sweep
    qreal acc = diff.length() / 100.0;



    // Calculate new rotation axis as weighted sum
    rotationAxis = (rotationAxis * angularSpeed + n * acc).normalized();

    // Increase angular speed
    angularSpeed += acc;
}
//! [0]

//! [1]
void LiveWidget::timerEvent(QTimerEvent *)
{

    // Update scene
    paintGL();
}

void LiveWidget::initFrameBuffer()
{
    framebuffer = new QOpenGLFramebufferObject(RES_X,RES_Y);
}

//! [1]

void LiveWidget::initializeGL()
{
    initializeOpenGLFunctions();

    initFrameBuffer();
    //qglClearColor(Qt::black);
    initShaders();
    initCelularWorld(10);


//! [2]
    // Enable depth buffer
    glEnable(GL_DEPTH_TEST);

    // Enable back face culling
    glEnable(GL_CULL_FACE);
//! [2]


    sprite.init();

    // Use QBasicTimer because its faster than QTimer
    timer.start(10, this);
}

//! [3]
void LiveWidget::initShaders()
{
    initTextures();
    // Compile vertex shader
    if (!program.addShaderFromSourceFile(QOpenGLShader::Vertex, ":/vshader.glsl"))
        close();

    // Compile fragment shader
    if (!program.addShaderFromSourceFile(QOpenGLShader::Fragment, ":/fshader.glsl"))
        close();

    // Link shader pipeline
    if (!program.link())
        close();

    // Bind shader pipeline for use
    if (!program.bind())
        close();
}
//! [3]

//! [4]
void LiveWidget::initTextures()
{
    texture1 = new QOpenGLTexture(QImage(":/cube.png"));
}
//! [4]

//! [5]
void LiveWidget::resizeGL(int w, int h)
{
    RES_X = w; RES_Y = h;
    // Set OpenGL viewport to cover whole widget
    glViewport(0, 0, w, h);

    // Calculate aspect ratio
    qreal aspect = qreal(w) / qreal(h ? h : 1);

    // Set near plane to 3.0, far plane to 7.0, field of view 45 degrees
    const qreal zNear = 0.0, zFar = 1000.0, fov = 45.0;

    // Reset projection
    projection.setToIdentity();

    // Set perspective projection
    //projection.perspective(fov, aspect, zNear, zFar);
    projection.ortho(-1,1,-1,1,zNear,zFar);
    projectionScreen = projection;
}
//! [5]

void LiveWidget::initCelularWorld(int densityInPercent)
{
    QImage celImage(RES_X,RES_Y, QImage::Format_ARGB32);
    for(int i = 0; i < RES_X; i++)
        for(int j = 0; j < RES_Y; j++ )
        {
            uint col = 0xFFFFFFFF;
            if(rand()%100 < densityInPercent )
                col = 0xFF000000;
            celImage.setPixel(i,j,col);

        }

    texture1 = new QOpenGLTexture(celImage);

    glEnable(GL_TEXTURE_2D);
    //texture = bindTexture(celImage);
    //texture = bindTexture(QImage(":/cube.png"));
    texture1->bind();
    //glBindTexture(GL_TEXTURE_2D, celImage);

    // Set nearest filtering mode for texture minification
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);

    // Set bilinear filtering mode for texture magnification
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

    // Wrap texture coordinates by repeating
    // f.ex. texture coordinate (1.1, 1.2) is same as (0.1, 0.2)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);

    bNeedReinitTexture = true;

}


void LiveWidget::paintGL()
{

    if(!framebuffer) return;
    n_frame++;
    qDebug() << n_frame;
    // Calculate model view transformation
    QMatrix4x4 matrix;
    matrix.translate(0.0, 0.0, -5.0);
    matrix.rotate(rotation);

    framebuffer->bindDefault();
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    program.setUniformValue("mvp_matrix", projectionScreen * matrix);
    if( bNeedReinitTexture )
    {
        glBindTexture(GL_TEXTURE_2D, texture);
    }
    else
        glBindTexture(GL_TEXTURE_2D, framebuffer->texture());
    program.setUniformValue("texture", 0);
    program.setUniformValue("fbo_pass",0);
    program.setUniformValue("n_frame",n_frame);
    program.setUniformValue("RES_X",RES_X);
    program.setUniformValue("RES_Y",RES_Y);
    sprite.drawSprite(&program);


    //return;

    framebuffer->bind();
    if( bNeedReinitTexture )
    {
        //glBindTexture(GL_TEXTURE_2D, texture);
        texture1->bind();
        bNeedReinitTexture = false;
    }
    else
        glBindTexture(GL_TEXTURE_2D, framebuffer->texture());
    //glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    program.setUniformValue("mvp_matrix", projection * matrix);
    program.setUniformValue("texture", 0);
    program.setUniformValue("fbo_pass",1);
    QVector4D color((float)rand()/RAND_MAX, (float)rand()/RAND_MAX, (float)rand()/RAND_MAX, 1);
    program.setUniformValue("color",color);
    sprite.drawSprite(&program);
    framebuffer->toImage().save("frames/frame"+QString::number(n_frame)+".png");
    //framebuffer->release();


}
