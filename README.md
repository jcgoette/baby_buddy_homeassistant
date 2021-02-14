# baby_buddy_homeassistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This custom integration provides sensors for [Baby Buddy](https://github.com/babybuddy/babybuddy) API endpoints within [Home Assistant](https://github.com/home-assistant/core).

## Installation

### HACS

1. Go to any of the sections (integrations, frontend, automation).
1. Click on the 3 dots in the top right corner.
1. Select "Custom repositories"
1. Add the URL (i.e., https://github.com/jcgoette/baby_buddy_homeassistant) to the repository.
1. Select the Integration category.
1. Click the "ADD" button.

## Configuration

### Parameters
| Name | Type | Description |
|------|:----:|-------------|
| address ***(required)*** | string |   Web address that hosts your instance of Baby Buddy.
| api_key ***(required)*** | string |  The API key from the user settings page on your instance of Baby Buddy.
| ssl ***(optional)*** | boolean |  Whether address is HTTPS enabled or not. Defaults to True.
| sensor_type ***(optional)*** | list |  List of Baby Buddy API endpoints to create sensors for. Defaults to all currently available [Baby Buddy API endpoints](https://github.com/babybuddy/babybuddy#api).

### Example
```yaml
sensor:
 - platform: babybuddy
   address: baby.example.com
   api_key: !secret babybuddy_api_key
   sensor_type:
    - changes
    - feedings
```
