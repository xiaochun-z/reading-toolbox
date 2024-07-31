These python script can:

* convert images files to pdf file, you can also limit the max pages of your pdf file, this is for kindle when the pdf file is too huge, switching between pages on kindle can be a problem.
* split a pdf file into different pdf files, this is also for some huge pdf file, kindle cannot open huge pdf  smoothly.
* merge pdf files into a single pdf, this is for some pdf files which only contains a single chapter, but you have dozens of chapters, merge these pdf files into a single pdf file make it easier to read.
* spiders folder: this is a folder which contains some spiders to crawl online commics for you, some websites will provide commics free for you to read, but you probably want to download these images in a batch and convert these images into a pdf. this is the reason why I started to write the spiders. Unfortuately, each website is different, so downloading images will be different, you can use these existings spiders as a reference to write a new spider for a different website.

# img2pdf for Kindle Scribe
Simple Python script to convert a set of images to PDF and combine them into one single PDF file for Kindle Scrible within seconds.
Usage:
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r .\requirements.txt 
python img2pdf.py c:/downloads/folder-contains-jpgs-pngs/ c:/downloads/output.pdf
```
# split a huge pdf to serval smaller pdf files

Kindle cannot handle very huge file, so we cut it into pieces.

```bash
# parameter: source file, folder to store the new files, page size(100 pages for each pdf)
python .\split_pdf.py "c:/downloads/a-very-big.pdf" "c:/downloads/new-files-folder/" 100
```

# merge serveral pdf files into a single pdf file

I don't want to store a lot of pdf files in my kindle, they're too many so I want to merge them into a single one.

```bash
python .\merge_pdf.py "c:/downloads/a-folder-contain-many-pdf-files/" "c:/downloads/merged_pdf.pdf"
```

# example to scrape commics from a website
this is an example to use selenium for scrape commics from a website, it demostrated how to get all the images and download them, after finished this chapter, it will go to next chapter and continue.
```bash
python .\spiders\mhz.py
python .\spiders\92mh.py
```
