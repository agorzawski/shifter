# ESS OP Shifter Changelog

### v.0.4.7
- fixed the 'now on shift' and 'update-ioc' data fetch, to follow the shifts overlap

### v.0.4.6
- added team view calendar
- added summarised working hours calculator  (day/off/nights)

### v.0.4.5
- added dismissible messages for the main display (editable from the django admin)
- fixed the default redirect
- extra message for the test/production server

### v0.4.4
- users login/logout support
- user's shift visible under 'My shift'
- ical export time zone fix (aligned with the rest of the system)

### v0.4.3
- shiftID generation fixed
- SL displayed in yellow in the global calendar

### v0.4.2
- color legend for the calendar view
- removed unused labels on the 'todays view'

### v0.4.1
- configurable color of the shift slot

### v0.4
- Integration with LDAP (names/ phone numbers/ emails/ pictures)
- Exposed JSON with the current shift crew for the shift update tool
- Newer version of fullcalendar + bootstrap
- Repository integration action buttons
- Refreshed look: new nav bar including grouping of the action buttons and hiding unused when not logged in.

### v0.3
- Added moving existing shifts/campaigns (admin action)
- Newer version of the fullcalendar scripts

### v0.2
- Logged user's shifts displayed as individual calendar and available as .ical files
- Included import forms for simple schedules (admin action)

### v0.1
- Initial import
- Basic calendar display