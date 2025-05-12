@echo off
setlocal

:: Get current directory (bat file location)
echo Determining target directory...
for %%I in ("%~dp0.") do set "TARGET=%%~fI"
echo Target directory is: %TARGET%

:: Define source path
echo Setting source directory...
set "SOURCE=\\Desktop-g3eiii5\timeline\JAYLIN\software\skein-care"
echo Source directory is: %SOURCE%

:: Use robocopy to copy and replace all contents
echo Starting file copy with robocopy...
robocopy "%SOURCE%" "%TARGET%" /E /COPY:DAT /R:2 /W:2

:: Check robocopy exit code
echo Robocopy finished with exit code %ERRORLEVEL%

endlocal
pause
