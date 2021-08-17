# baby_buddy_homeassistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

This custom integration allows you to monitor [Baby Buddy](https://github.com/babybuddy/babybuddy) data for your child within [Home Assistant](https://github.com/home-assistant/core). It also allows you to start timers and add data entries from within Home Assistant.

## Installation

### HACS

1. Navigate to integrations section.
1. Click "Explore & Add Repositories" in the bottom right corner.
1. Search for "Baby Buddy".
1. Click "INSTALL THIS REPOSITORY IN HACS".
1. Click "Install".

## Configuration

Adding BabyBuddy to your Home Assistant instance can be done via the user interface. The below parameters are required.

### Parameters

| Name | Optional | Description |
|------|:----:|-------------|
| address  | no |   Full URL host for your instance of Baby Buddy.
| port  | no |   Host port (default=8000)
| api_key| no |  The API key from the user settings page on your instance of Baby Buddy.

### Options

The following options are available:

- Temperature unit (celsius or fahrenheit)

- Weight unit (Kilogram or Pounds)

- Feeding amount volume unit (ml or oz)

- Update interval in seconds (default=60)

## Integration Entities

This integration provides the following entities.

### Sensors

- A sensor entity for each child with the child name and age showing as state.

- A sensor for each child **last** data entry including `diaper_change`, `feeding`, `sleep`, `tummy_time`, `temperature` and `weight`.

### Switches

- A switch is created for each child to handle its `timer`. Turning on the switch starts a new timer for the linked child. Turning off the switch deletes the timer. (check below for usage of timer.)

### Timer notes

`Feedings`, `Sleep` and `Tummy time` can be linked to a timer. If a timer is active you can add any of these entries and link it to the timer to automatically specify child, start and end times. It is important that the timer is active when the service is called.

## Services

### SERVICE ADD_CHILD

This service adds a new child. At least one child should be added to start seeing the different sensors and switches.

| Service data attribute | Optional | Description |
|------|:----:|-------------|
| first_name | no |   Baby's first name.
| last_name | no |   Baby's last name.
| birth_date | no |   Child's birth date in YYYY-MM-DD format.

### SERVICE START_TIMER

This service starts a new timer for specified child with optional starting time.

| Service data attribute | Optional | Description |
|------|:----:|-------------|
| entity_id | no |   entity_id for the switch linked to the child.
| start | yes |   Specify start time (must be in the past) else now() will be used.
| name | yes |   Optional name for new timer.

### SERVICE ADD_FEEDING

This service adds a feeding entry for your child. Feeding start/end/child fields can be linked to an active timer.

| Service data attribute | Optional | Description |
|------|:----:|-------------|
| entity_id | no |   entity_id for the timer switch linked to the child.
| type | no |   Specify type of feeding. Can be one of `Breast milk`, `Formula`, `Fortified breast milk` or `Solid food` (default= `Breast milk`).
| method | no |   Specify method of feeding. Can be one of `Bottle`, `Left breast`, `Right breast`, `Both breasts`, `Self fed` or `Parent fed` (default= `Both breasts`).
| timer | yes |   set to True to use the currently active timer.
| start | yes |   Specify start time (must be in the past) else now() will be used. This can be ignored if timer is used.
| end | yes |   Specify end time (must be in the past) else now() will be used. This can be ignored if timer is used.
| amount | yes |   Specify amount of feeding as an integer.
| notes | yes |   Add notes text to entry.

### SERVICE ADD_SLEEP

This service adds a sleep entry for your child. Sleep start/end/child fields can be linked to an active timer.

| Service data attribute | Optional | Description |
|------|:----:|-------------|
| entity_id | no |   entity_id for the timer switch linked to the child
| timer | yes |   set to True to use the currently active timer.
| start | yes |   Specify start time (must be in the past) else now() will be used. This can be ignored if timer is used.
| end | yes |   Specify end time (must be in the past) else now() will be used. This can be ignored if timer is used.
| notes | yes |   Add notes text to entry.

### SERVICE ADD_TUMMY_TIME

This service adds a tummy time entry for your child. Tummy time start/end/child fields can be linked to an active timer.

| Service data attribute | Optional | Description |
|------|:----:|-------------|
| entity_id | no |   entity_id for the timer switch linked to the child
| timer | yes |   set to True to use the currently active timer.
| start | yes |   Specify start time (must be in the past) else now() will be used. This can be ignored if timer is used.
| end | yes |   Specify end time (must be in the past) else now() will be used. This can be ignored if timer is used.
| milestone | yes |   Add milestone text to entry.

### SERVICE ADD_DIAPER_CHANGE

This service adds a diaper change entry for your child.

| Service data attribute | Optional | Description |
|------|:----:|-------------|
| entity_id | no |   entity_id for the child sensor.
| type | no |   Specify type of diaper. This can be `Wet` or `Solid`.
| time | yes |   Specify diaper change time (must be in the past) else now() will be used.
| color | yes |   Specify diaper color.  This can be `Black`, `Brown` , `Green` or `Yellow`.
| amount | yes |   Add number of diapers.
| notes | yes |   Add notes text to entry.

### SERVICE ADD_TEMPERATURE

This service adds a temperature entry for your child.

| Service data attribute | Optional | Description |
|------|:----:|-------------|
| entity_id | no |   entity_id for the child sensor.
| temperature | no |   Specify temperature value (float).
| time | yes |   Specify temperature recording time (must be in the past) else now() will be used.
| notes | yes |   Add notes text to entry.

### SERVICE ADD_WEIGHT

This service adds a weight entry for your child.

| Service data attribute | Optional | Description |
|------|:----:|-------------|
| entity_id | no |   entity_id for the child sensor.
| weight | no |   Specify weight value (float).
| date | yes |   Specify weight recording date (YYYY-MM-DD format) else today() will be used.
| notes | yes |   Add notes text to entry.