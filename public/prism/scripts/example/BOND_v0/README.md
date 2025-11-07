# Example BOND 

## Init your BOND board

Use Arduino IDE to program BOND for the first time.

See [BOND_v0/README.md](BOND_v0/README.md) for details.

Also see `bond_progfresh_0.scr`

## How to use this Example

### Create your own product folder

For your own use of BOND, copy this folder to a new location, and modify the files as needed.
For example, create your product folder,


    martin@martin-ThinkPad-L13-Gen-2a:~/git/scripts/public/prism/scripts$ mkdir myproduct
    martin@martin-ThinkPad-L13-Gen-2a:~/git/scripts/public/prism/scripts$ cp -R example/BOND_v0/ myproduct/blt
    martin@martin-ThinkPad-L13-Gen-2a:~/git/scripts/public/prism/scripts$ ll
    total 20
    drwxrwxr-x 4 martin martin 4096 Nov  7 10:18 ./
    drwxrwxr-x 5 martin martin 4096 Sep 10 09:45 ../
    drwxrwxr-x 8 martin martin 4096 Oct 14 16:58 example/
    -rw-rw-r-- 1 martin martin   48 Aug 18 19:53 __init__.py
    drwxrwxr-x 3 martin martin 4096 Nov  7 10:19 myproduct/


### Create Pogo Board to BOND Header Mapping

In your new product folder, edit the file `public/prism/scripts/myproduct/blt/assets/pogo_hdr_definition._json`


