0.0.4 - Fully integrated python-goose library into newspaper. Article objects
        now have much more options. All configurations are now based on Configuration()
        objects which can be passed into Source or Article objects. Default configuration
        setups make this easy. Added simple multithreading article download framework.

0.0.5 - Fixed seamless configuration api for Article and Source objects. Enabled multi language
        support in 10+ languages including non-western languages like Arabic, Korean, Chinese.
        Fixed bug where we made a wrong assumption of calling .text from the requests module.
