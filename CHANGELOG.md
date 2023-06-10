# ESS OP Shifter Changelog

### v.1.0.8
- Statistics per MyTeam and detailed panel for Rota Maker,
- Few cosmetics between calendars default views: hiding/showing relevant events depending on the page,
- shift inconsistencies - shift-to-shift hours break,
- individual ical links enhanced with shift companion contact details,

### v.1.0.7 (including .1-.6)
- User/Team inconsistencies improved,
- Show shift companion, 
- Study details exposed with direct link, id and indiv pages,
- Fixes for sorting tables, 
- Admin actions for batch shifts/studies actions,
- Refreshed Today page with upcoming shift,
- Study overviews, tables & views,
- User-friendly tables (default rows increased)

### v.1.0.0
- Beam studies planner (ACCOP-337) first version,
- Shifter's Desiderata for shift planning,
- Shifter's view allow to display/compare with future plannings,
- Refreshed look to follow the latest Full Calendar, 
  - Internal: fixes improving the calendar displays and data sources,
  - Internal: moved to npm packages with statics,

### v.0.9.3
- Bug removal on sorting the shifts for active shift/work time calcs.

### v.0.9.2
- Daily/weekly break limits highlighted in the user page,
- Additional filter for the off-control room roles, i.e. office assignments not displayed by default for the general overview, not affecting individual/team views,
- Performance fix to fetch only last campaigns' shifts within the last revision (main calendar refresh, not affecting individual/team views)
- Filter/display menu bar reworked,
- Few bugs fixed: 
  - Ldap provider,  
  - Upload new schedules with default revision,
  - ShiftID bug: NWH excluded when another shifts scheduled (sometimes wrong ID when morning, afternoon and normal working hours overlap),
  - Active shift JSON returns roles configured via os setting, not hardcoded. Extended by  default to StudyLeader, 

### v.0.9.1
- Asset page display/filter improvement (ACCOP-276)
- Fixed iCal links and its content (locations)
- bug fixes (more tests to ShiftID)

### v.0.9.0
- Simple OP Asset Management (ACCOP-225)
    - log of use,
    - different asset types, 
    - check in/check out.
- Improved the test coverage on the logical parts of the tool (HRCodes/ActiveShift/ShiftID)
    - Functional code splits, simplification and refactoring
    - Fixed 'default' ShiftID reported
- Admin pages refit (additional filters)
- Domain objects page revisited (admin/environment)
    - Predefined shift pattern switch

### v.0.8.2
- admin site style fix (whitenoise&gunicorn)

### v.0.8.1
- bugfix

### v.0.8.0
- support for ShiftIDs (history, browse)

### v.0.7.2
- missing holidays support (for HR codes and for the calendar display)
- admin group move to NWH (default) time slot

### v.0.7.1
- bugfix for the LDAP -> local DB save (difference between SQLite and Postgres)
- bugfix for the DEBUG flag

### v.0.7.0
- internal cache for members details from LDAP when calling /today or /ioc-update
- exposed member/team calendar links
- for the case of long breaks between shifts (i.e. missing night shifts) an extended 
    search (up to 2h prior to the new shift) is included
- bugfix: users and teams details shown for not authenticated calls
- added account password reset with the email support

### v.0.6.0
- shift time codes counts and display (ESS specific)
- shift import adjustments/fixes
- navigation menu expanded (teams)
- team's view revisited with collapsable table
- shiftId api exposed by date & time (beta)
- ioc setup data fixed for outside the/not found the active shift data

### v.0.5.7
- view & upload bugfixes
- doc update

### v.0.5.6
- exposed 'users' view (including ical get)
- exposed 'team's' view

### v.0.5.5
- bugfix on ical link

### v.0.5.4
- cleanup on phonebook entries style and sorting
- updated production/development server indications

### v.0.5.3
- bug fixes
- doc update

### v.0.5.2
- fixes for code quality issues (sonarqube report before deploying to production)
- fix for the phone number formatting
- added extended view on the team's shift breakdown

### v.0.5.1
- fix for the Today's page (now again includes all slots at given moment)
- minor bugs correction (found thanks to sonar scan)
- prepared for the docker releases
- included gitlab CI/CD

### v.0.5.0
- LDAP functionality extended, a separate phonebook available /phonebook (no auth needed)

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