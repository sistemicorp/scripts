How to make docs:

If not already installed:
   sudo apt-get install python3-sphinx

martin@martin-Lenovo-YOGA-900-13ISK2:~/sistemi/git/scripts/docs$ rm -rf build/
martin@martin-Lenovo-YOGA-900-13ISK2:~/sistemi/git/scripts/docs$ make html
Running Sphinx v1.8.5
making output directory...
building [mo]: targets for 0 po files that are out of date
building [html]: targets for 22 source files that are out of date
updating environment: 22 added, 0 changed, 0 removed
reading sources... [100%] prism_travellers
looking for now-outdated files... none found
pickling environment... done
checking consistency... done
preparing documents... done
writing output... [100%] prism_travellers
generating indices... genindex
writing additional pages... search
copying images... [100%] static/micropythonboard_a0103.PNG
copying static files... done
copying extra files... done
dumping search index in English (code: en) ... done
dumping object inventory... done
build succeeded.

The HTML pages are in build/html.
martin@martin-Lenovo-YOGA-900-13ISK2:~/sistemi/git/scripts/docs$ ll build
total 16
drwxr-xr-x 4 martin martin 4096 Jun  3 21:48 ./
drwxr-xr-x 4 martin martin 4096 Jun  3 21:48 ../
drwxr-xr-x 2 martin martin 4096 Jun  3 21:48 doctrees/
drwxr-xr-x 5 martin martin 4096 Jun  3 21:48 html/


If there are any other directories in /build, remove them.

Good links for info:
https://www.docslikecode.com/articles/github-pages-python-sphinx/
https://github.com/sphinx-doc/sphinx/issues/3382

Ver