# baby_buddy_homeassistant

This custom integration provides sensors for Baby Buddy API endpoints
=======

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

This custom integration provides sensors for Baby Buddy API endpoints.

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
| address ***(required)*** | string |   Web address that hosts your instance of BabyBuddy. *Must* be https enabled.
| api_key ***(required)*** | string |  The API key from the user settings page on your instance of BabyBuddy.

### Example
```yaml
sensor:
 - platform: babybuddy
   address: baby.example.com
   api_key: !secret babybuddy_api_key
```