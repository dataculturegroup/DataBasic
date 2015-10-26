#! /usr/bin/env bash
set -e

# thanks to georgeslabreche
# https://github.com/georgeslabreche/flask-babel/blob/master/install.sh

if [ "$(whoami)" != "root" ]; then
  echo "You need root access. Run this script again with sudo."
  exit 1
fi

# check python version, should be over 2.7
ret=`python -c 'import sys; print("%i" % (sys.hexversion<0x02070900))'`
if [ $ret -eq 0 ]; then
    echo "Required version of Python already installed."
else
	# this block untested
	echo "You need to install Python 2.7.X"
    echo -e "Install Python 2.7.10? [y/n] \c "
    read word
    if [ $word == "y" ]; then
       echo `wget http://python.org/ftp/python/2.7.10/Python-2.7.10.tar.bz2`
       echo `tar xf Python-2.7.10.tar.bz2`
       cd Python-2.7.10
       echo `./configure --prefix=/usr/local`
       echo `make && make altinstall`
       echo `rm Python-2.7.10.tar.bz2`
     else
       echo "Aborting installation script."
       exit 1
    fi
fi

# test whether virtualenv is installed
echo "Testing whether virtualenv is installed..."
if [ ! -d $"venv" ]; then
   echo "You need to install virtualenv"
   echo -e "Install virtualenv? [y/n] \c "
   read word
   if [ $word == "y" ]; then
      echo "This will install virtualenv in your home directory"
      echo "Installing virtualenv..."
      echo `pip install virtualenv`
      echo `virtualenv venv`
   fi
fi

# start virtual env and install flask
echo "Starting virtual environment"
alias activate=". venv/bin/activate"
pip install -r requirements.txt
python -m nltk.downloader punkt
python -m nltk.downloader stopwords
echo "Creating settings.py for this instance"
echo "SECRET_KEY='yoursecretkey'" > config/settings.py
echo "Installation complete."

