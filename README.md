# Customer-EMC-NFV-Phase1
This repository holds all of the shells and orchestration drivers required for phase 1.

Everything is private.

Usage:
Download the whole folder.
Run the "create package.cmd" to create a CloudShell package zip file with all of the scripts and meta data.
Some of the shells and drivers needs to be compiled inside the CloudShell Authoring tool to get the latest version of them copied to the package, such as:
Drivers\Shells\vCD\vcd_setup
Drivers\Shells\OnRack
Drivers\Orchestration\NVF Environment Driver

Another output of this cmd is the site-packages.zip, this is a file that needs to be extracted on tha CloudShell vm, under:
C:\Program Files (x86)\QualiSystems\TestShell\ExecutionServer\python\2.7.10\Lib\site-packages

The inputs excel file under Inputs needs to be filled with all of the relevant information and copied to the CloudShell vm, under:
c:\deploy

For more information, read the document file under Documentation
