# Saphety sin-pull
#Run
>python sin-pull.py (...)

#HELP
* [--help] to see a list of help.
* [--y] to say yes to all. Silent mode
* [--readed] to see only de readed documents.
* [--folder] to defined a folder to save the files, based on the current file folder. Ex: \SaphetyPull
* [--username] to defined your username. Ex: --username saphety
* [--password] to defined your password. Ex: --password invoice_network
* [--startDate] to defined your start date. Ex: --startDate 2021-01-01
* [--endDate] to defined your end date. Ex: --endDate 2022-01-01
* [--company] to defined your associated company. Ex: --company PT507957547
* [--content] to defined your return file type. You can choose between PDF and UBL21. Ex: --content PDF
* [--fileNamePattern] to defined the final file name. Use the next tags to change the file name.
**  [DocType] - Document type
**  [DocNumber] - Document number (unique)
**  [DocID] - Document ID  (unique)
**  [DocSender] - Document sender VAT
**  [DocDestination] - Document destination VAT
**  [DocDate] - Document date
**  EXAMPLE:
***   Command > ... --fileNamePattern DocType-DocNumber 
***   Result  > INVOICE-12345.xml 

#FULL EXAMPLE
> pull_integration.py --username saphety --password invoice_network --startDate 2021-01-01 --readed --fileNamePattern DocType-DocNumber --content PDF

#LOGS
* You can see the log file in the current file folder. File name: sin-pull.log
