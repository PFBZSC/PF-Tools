@echo off
:: 将参数透传给 main.py，%* 代表所有参数
python "%~dp0main.py" %*