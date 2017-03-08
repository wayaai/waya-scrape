# waya-scrape

## Getting started

```python
pip install -U -r requirements.txt
python setup.py develop
```

Download chrome driver (or whatever browser you are using with `Selenium`) https://sites.google.com/a/chromium.org/chromedriver/downloads.

If you're having trouble with `Selenium` take a quick look at this: https://github.com/SeleniumHQ/selenium/wiki/Getting-Started.

```python
python main.py
```

## Storing data sets

Data sets should be stored in the form:

```python
<DATASET_NAME>.zip/
    dataset_info.txt  # Human readable text file describing all pertinent info regarding the data set.
    details.pickle  # Dictionary w/ data_sample file names as keys (usually randomly generated uuids) and all available meta-data as values. Used to sort data sets amongst other things.
    data_sample_0
    ...
    data_sample_n
```

## High-level doc

When we are scraping we want to save all relevant meta-data along with the images. This will be needed and very important when we are sorting the data later and using it to train our networks. Our current standard way of doing this is to store this info in a dictionary and [serialize](https://docs.python.org/2/library/pickle.html) the dict and store it to disc. For each scraped image we generate a unique, random uuid for it that serves as its file name and dict key.

```javascript
uuid: { search_engine: , keywords: , image_url: , phash: }
```

phash is calculated for each image upon downloading and is used to detect duplicate images. maybe we can find a better way to do this
