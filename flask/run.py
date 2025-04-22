from scansnap import app

if __name__ == '__main__':
    app.run(
        debug=True,

        # Allow access from another computer on the same network
        # Example: you can run the app on your laptop and open
        # the app from your smartphone
        host='0.0.0.0',

        # Will this do the trick?
        use_reloader=False
        )
