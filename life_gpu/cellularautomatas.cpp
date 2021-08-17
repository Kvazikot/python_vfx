#include "cellularautomatas.h"
#include <QPainterPath>
#include <QPainter>
#include <QDebug>
#include <QtConcurrent>
#include <QFuture>

std::map<std::pair<int,int>, Cell*> CellularAutomatas::cmap;

Cell::Cell()
{
    value = 0;
}

Cell::Cell(int ii, int jj): i(ii), j(jj)
{
    value = 0;
}

void CellularAutomatas::CreateWorld(int cellsX, int cellsY)
{
    for(int i = 0; i < cellsX; i++)
        for(int j = 0; j < cellsY; j++ )
        {
            Cell* cell = new Cell(i,j);
            if(rand()%100 < 10 )
                cell->value = 1;
            else
                cell->value = 0;
            cells.push_back(cell);
            cmap[std::make_pair(i,j)] = cell;
        }

    for(int i = 0; i < cellsX; i++)
    for(int j = 0; j < cellsY; j++ )
    {
        Cell* cell = cmap[std::make_pair(i,j)];
        for(int k = -1; k <= 1; k++ )
        for(int l = -1; l <= 1; l++ )
        {
            //if(k!=0 && l!=0)
            {
                if( cmap.find( std::make_pair(i+k,j+l))!=cmap.end() )
                {
                    Cell* neibour = cmap[std::make_pair(i+k, j+l)];
                    if(neibour!=cell)
                    {
                        cell->neibours.push_back(neibour);
                    }
                }
            }
        }
    }
    qDebug();



}

CellularAutomatas::CellularAutomatas(int cellsX, int cellsY)
    :cellsX(cellsX),cellsY(cellsY)
{
    bDrawGrid = true;
    bFastDraw = false;
    cells.clear();
    cmap.clear();
    n_generation = 0;
    n_live = 0;
    CreateWorld(cellsX, cellsY);
}

void CellularAutomatas::DrawCells(QImage& image)
{
    int cell_size = image.width() / cellsX;

    QPainter painter(&image);

    painter.translate(cell_size/2, 0);
    painter.scale(0.98,0.98);
    QRect r = image.rect();
    painter.setPen(Qt::black);
    painter.setBrush(Qt::red);
    painter.fillRect(image.rect(), Qt::red);
    painter.drawRect(r);

    if(bFastDraw)
    {
        std::map<std::pair<int,int>, Cell*>::iterator it_cell;
        for(it_cell = cmap.begin(); it_cell!=cmap.end(); it_cell++)
        {
            Cell* cell = (*it_cell).second;
            QPoint C( cell->xpix, cell->ypix );
            if(cell->value!=0)
            {
               QColor c(Qt::black);
               c.setAlpha(255);
               image.setPixel(C.x(),C.y(),c.value());
            }
        }
        return;
    }

    for(int i=0; i < cellsX; i++)
    for(int j=0; j < cellsY; j++)
    {
       if( cmap.find(std::make_pair(i,j))!= cmap.end() )
       {
           Cell* cell = cmap[std::make_pair(i,j)];
           cell->xpix = i * cell_size + cell_size/2;
           cell->ypix = j * cell_size + cell_size/2;
           int wall_width = 1;
           QPoint C( i * cell_size + cell_size/2, j * cell_size + cell_size/2 );
           if(cell->value!=0)
           {
               QPainterPath path;
               path.addEllipse(C,cell_size/2,cell_size/2);
               painter.fillPath(path, Qt::black);
           }
           if( bDrawGrid )
           {
               QRect wall_rc( C.x() - cell_size/2 , C.y() - cell_size/2  , wall_width, cell_size + wall_width );
               //painter.drawRect(wall_rc);
               painter.fillRect(wall_rc, Qt::blue);
               wall_rc = QRect( C.x() + cell_size/2 , C.y() - cell_size/2   , wall_width, cell_size + wall_width );
               //painter.drawRect(wall_rc);
               painter.fillRect(wall_rc, Qt::blue);
               wall_rc = QRect( C.x() - cell_size/2  , C.y() - cell_size/2 , cell_size + wall_width, wall_width );
               //painter.drawRect(wall_rc);
               painter.fillRect(wall_rc, Qt::blue);
               wall_rc = QRect( C.x() - cell_size/2 , C.y() + cell_size/2 , cell_size + wall_width, wall_width );
               //painter.drawRect(wall_rc);
               painter.fillRect(wall_rc, Qt::blue);
           }
       }
       else
           qDebug("missed %d %d", i, j);
    }


}



void Live_Rules(std::map<std::pair<int,int>, Cell*>::iterator i_start,
                                   std::map<std::pair<int,int>, Cell*>::iterator i_end)
{

    std::map<std::pair<int,int>, Cell*>::iterator it_cell;
    //for(int i=0; i < cellsX; i++)
    //for(int j=0; j < cellsY; j++)
    for(it_cell = i_start; it_cell!=i_end; it_cell++)
    {
        Cell* cell = (*it_cell).second;
        int n_live_neibours = 0;
        std::vector<Cell*>::iterator it;
        for(it=cell->neibours.begin(); it!=cell->neibours.end(); it++)
        {
            if( (*it)->value > 0 )
                n_live_neibours++;
        }
        if( (cell->value > 0) && (n_live_neibours < 2) ) // underpopulation
          cell->value = 0;
        if( (cell->value > 0) && (n_live_neibours > 3) ) // overpopulation
          cell->value = 0;
        if( (cell->value == 0) && (n_live_neibours == 3) ) //reproduction.
          cell->value = 1;
       // if(cell->value)
       //     n_live++;

        //if(n_live_neibours)
        //qDebug() << "n_live_neibours=" << n_live_neibours;

    }
}


void Live_Rules_Process( const CellularTaskInput& task )
{
    int cnt = 0;
    QElapsedTimer t;
    t.start();

   std::map<std::pair<int,int>, Cell*>::iterator it_cell;
    for(it_cell = task.i_start; it_cell!=task.i_end; it_cell++)
    {
        Cell* cell = (*it_cell).second;
        int n_live_neibours = 0;
        std::vector<Cell*>::iterator it;
        for(it=cell->neibours.begin(); it!=cell->neibours.end(); it++)
        {
            if( (*it)->value > 0 )
                n_live_neibours++;
        }

        if( (cell->value > 0) && (n_live_neibours < 2) ) // underpopulation
          cell->value = 0;
        if( (cell->value > 0) && (n_live_neibours > 3) ) // overpopulation
          cell->value = 0;
        if( (cell->value == 0) && (n_live_neibours == 3) ) //reproduction.
          cell->value = 1;
        cnt++;
    }

  // Live_Rules(task.i_start,task.i_end);
    qDebug() << "Live_Rules_Process " << cnt << " processed" << " time=" << t.elapsed();
    qDebug() << "thread " << QThread::currentThreadId();

}

QVector< CellularTaskInput > tasks;
QVector< CellularTaskInput > tasks2;

void CellularAutomatas::Live_Rules_Parallel()
{

    static const int THREAD_COUNT = QThread::idealThreadCount();
    int n_cells_in_thread = (cmap.size()) / (THREAD_COUNT);
    //for(int i=0; i < n_cells_in_thread; i++)
    int cnt = 0;
    auto i_start = cmap.begin();
    auto i_end = cmap.begin();
    tasks.clear();

    for(auto it_cell = cmap.begin(); it_cell!=cmap.end(); it_cell++)
    {
        if(cnt == n_cells_in_thread)
        {
            i_end = it_cell;
            CellularTaskInput task;
            task.cmap = &cmap;
            task.i_start = i_start;
            task.i_end = i_end;
            tasks.push_back(task);
            //Live_Rules_Process(task);
            i_start = i_end;
            cnt = 0;
        }
        cnt++;
    }


    QtConcurrent::blockingMap( tasks, Live_Rules_Process );
   // future.waitForFinished();
}


void CellularAutomatas::Draw(QImage &resultImage)
{
    resultImage.fill(Qt::white);
    DrawCells(resultImage);

}

void CellularAutomatas::NextFrame()
{
    n_live = 0;
    QElapsedTimer t;
    t.start();
    Live_Rules(cmap.begin(),cmap.end());
    //qDebug() << "Live_Rules " << t.elapsed();
    //t.restart();
    //Live_Rules_Parallel();
    //qDebug() << "Live_Rules_Parallel " << t.elapsed();
    n_generation++;
}
