#!/bin/bash
                                        #ADRESIP:PORT
gunicorn --threads 5 --workers 1 --bind 0.0.0.0:1935 overlayCamera:app