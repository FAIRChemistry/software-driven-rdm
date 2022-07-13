#!/bin/bash
# This script demonstrates how to use the API Generator. In order to perform
# API Generation it is necessary to point towards your markdown files (--path)
# and specify where the API (--name) will bne written (--out).
# 
# Markdown files are validated on the fly, thus you will notice where and what went
# wrong. 
#
# The following example generates a simple Biocatalyst module which incorporates
# several types of a Biocatalyst by using inheritance. Furthermore, such objects
# can also contain or be composed out of other objects, which will be shown here.
# 
# After generation you can inspect the resulting classes and use them right away.
# There will also be a "scheme" directory, where you can visualize the module using
# mermaid and also inspect the metadata this class uses.
#
# Jan Range - 10/Jul/2022

sdrdm generate --path ./specifications --out . --name pyBioCat