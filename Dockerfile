FROM mcr.microsoft.com/windows/servercore:ltsc2022

# Download and install Python 3.11
ADD https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe C:\python-3.11.8-amd64.exe
RUN C:\python-3.11.8-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

# Copy your pre-configured MetaTrader5 terminal into the container
COPY MetaTrader5 C:\MetaTrader5

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r forex-bot/requirements.txt

EXPOSE 8000

CMD ["python", "forex-bot/app/main.py"] 