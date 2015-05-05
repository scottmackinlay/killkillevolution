# killkillevolution
Softdes Final project

You need pygame to play this game: 
    $sudo apt-get install python.pygame

The code is run as follows

1.  Open a terminal window and find your IP

        $ ifconfig
    The IP youre interested in is in the wlan0 section under inet addr (eg: 10.2.43.128)

2.  Run the server code in a file that also has the PodSixNet folder.
        ~ python KKE_server.py 10.2.43.128:8000
    Where that IP is your personal IP you found in step 1. 8000 represents the port you connect to and I've found that 8000 works.

3.  Run the client code (and get your friends to run it too!)
        ~ python KKE_client.py 10.2.43.128:8000
    Again, use your IP followed by ":8000". You can have as many clients attached to the server as you want. (we've tested up to three)

Once the game is running, press enter to start. Use WASD to move, the cursor to aim and the mouse buttons to shoot.

Have fun!
