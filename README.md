# baby_buddy_homeassistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This custom integration provides sensors for [Baby Buddy](https://github.com/babybuddy/babybuddy) API endpoints within [Home Assistant](https://github.com/home-assistant/core).

## Installation

### HACS

1. Navigate to integrations section.
1. Click "Explore & Add Repositories" in the bottom right corner.
1. Search for "Baby Buddy".
1. Click "INSTALL THIS REPOSITORY IN HACS".
1. Click "Install".

## Configuration

### Parameters
| Name | Type | Description |
|------|:----:|-------------|
| address ***(required)*** | string |   Web address that hosts your instance of BabyBuddy.
| api_key ***(required)*** | string |  The API key from the user settings page on your instance of BabyBuddy.
| ssl ***(optional)*** | boolean |  Whether address is HTTPS enabled or not. Defaults to True.

### Example
```yaml
sensor:
 - platform: babybuddy
   address: baby.example.com
   api_key: !secret babybuddy_api_key
```
