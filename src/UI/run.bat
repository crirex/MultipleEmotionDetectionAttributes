@echo on
@echo Launching application...
@echo off
set /p theme_name="Use theme ([d]ark/[l]ight): "
python main.py --theme %theme_name%
