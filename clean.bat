@echo off
cd /d %~dp0

echo Deleting all .pdf files...
del /S /Q *.pdf

echo Deleting all .tex files...
del /S /Q *.tex

echo Deleting all intermediate LaTeX files...
del /S /Q *.aux
del /S /Q *.log
del /S /Q *.toc
del /S /Q *.out
del /S /Q *.bbl
del /S /Q *.blg
del /S /Q *.synctex.gz
del /S /Q *.txt

echo Cleanup complete.
pause