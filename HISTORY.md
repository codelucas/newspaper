0.0.4 - Fully integrated python-goose library into newspaper. Article objects
        now have much more options. All configurations are now based on Configuration()
        objects which can be passed into Source or Article objects. Default configuration
        setups make this easy. Added simple multithreading article download framework.

0.0.5 - Fixed seamless configuration api for Article and Source objects. Enabled multi language
        support in 10+ languages including non-western languages like Arabic, Korean, Chinese.
        Fixed bug where we made a wrong assumption of calling .text from the requests module.

0.0.6 - Fixed a bunch of small bugs in the source.py file (still need to update readme). Batch
        downloading articles was not setting the article is_downloaded boolean. I was also using
        the del keyword very irresponsibly... Made many modifications where the source object
        had to filter out urls. Mostly replaced with list comprehensions. 
        Added a pull request from Alex K. where he added an option for just the article html
        extraction. Feel free to toggle this option in the configs. I have yet to add this to the
        docs once again.
