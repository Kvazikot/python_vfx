#ifndef CELLULARAUTOMATAS_H
#define CELLULARAUTOMATAS_H

#include <QImage>
#include <QProgressBar>
#include <QGraphicsScene>
#include <vector>
#include <map>

// клетка
struct Cell
{
    int   i,j;
    int   xpix, ypix;
    int   value;
    Cell();
    Cell(int ii, int jj);
    void setIJ(int ii, int jj){ i=ii; j=jj;}
    bool isNull();
    std::vector<Cell*> neibours;

};

//задача для паралельной обработки клеток
struct CellularTaskInput {
/*    CellularTaskInput(){}
    CellularTaskInput(std::map<std::pair<int,int>, Cell*>* cmap,
                      std::map<std::pair<int,int>, Cell*>::iterator i_start,
                      std::map<std::pair<int,int>, Cell*>::iterator i_end)
        :cmap(cmap),i_start(i_start),i_end(i_end)
    {
    }
*/
    std::map<std::pair<int,int>, Cell*>* cmap;
    std::map<std::pair<int,int>, Cell*>::iterator i_start;
    std::map<std::pair<int,int>, Cell*>::iterator i_end;
};


class CellularAutomatas
{
public:
    int cellsX;
    int cellsY;
    int n_generation;
    int n_live;
    bool bDrawGrid;
    bool bFastDraw;
    std::vector<Cell*>   cells;
    static std::map<std::pair<int,int>, Cell*> cmap;
    CellularAutomatas(int cellsX, int cellsY);
    void CreateWorld(int cellsX, int cellsY);
    void NextFrame();
    void Live_Rules_Parallel();
    void Draw(QImage& resultImage);    
    void setDrawGrid(bool flag){ bDrawGrid = flag; }
    void setFastDraw(bool flag){ bFastDraw = flag; }
    void DrawCells(QImage& image);
    void DrawToScene(QGraphicsScene* scene, QProgressBar* progress, bool bWithDelay);
};

#endif // CELLULARAUTOMATAS_H
