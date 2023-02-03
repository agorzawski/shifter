# Shifter
A simple system for displaying shift schedules (via web server) and for managing/handling shift planning, including:
- members, roles, teams,
- campaigns, time slots, 
- assigned shifts,
- provides simple way of booking additional members slots (eg. studies, visits).

### Members/Teams views
Logged-in users are able to see:

- personal planning,
  - present schedule,
  - future revisions,
- personal shift breakdown (with some statistics),
- personal and team links to the online calendars to subscribe via Outlook or Calendar,
- team planning with team breakdown and statistics.


### Asset ledger
Users can make use of the shared assets (eg. cars, keys), the full asset application in `{your.address.com}/assets`.

### Study plannings

Along with the planned shifts, the associated studies/other activities can be planned and arranged. 
The dedicated app is available under `{your.address.com}/studies`

The planning for the studies is displayed in the full calendar view and the user's planning view 
for the relevant studies that are either users or collaborated.


### System links

There are few endpoints that allow to get data about the planning in `json` format:
- `{your.address.com}/ioc-update` **current shift crew and shift**,
- `{your.address.com}/shifts`, the **list of shiftIds that took place** i.e., the system was,

    ```json
    {
    ids: [
      "20221217A",
      "20221216A",
      "20221205B",
      "20221124A",
      (...)
      ]
    }
    ```
  - `{your.address.com}/shifts?id={shiftId}`, the **shiftId info and the previous and the next shift** Ids,
   
      ```json lines
      {
        SID: "20221217A",
        status: "True",
        prev: "20221216A",
        next: null
      }
      ```

- `{your.address.com}/scheduled-work-time` **all scheduled time for the current revision** including the total scheduled work hours, 
    ```json
    {
      startDate: null,
      endDate: null,
      totalWorkingH: 4576,
      workingSlots: [
        ...
      ]
    }
    ```

  - `{your.address.com}/scheduled-work-time?start=YYYY-MM-DD&end=YYYY-MM-DD`all scheduled time for the current revision 
     between dates `start` and `end`. 
       ```json
       {
       startDate: "2022-12-16 00:00:00",
       endDate: "2022-12-21 00:00:00",
       totalWorkingH: 17,
       workingSlots: [
         [
           "2022-12-16 08:00:00",
           "2022-12-16 16:30:00"
         ],
         [
           "2022-12-17 08:00:00",
           "2022-12-17 16:30:00"
         ]
       ]
       }
       ```


## Planning/editing
- Users can express their constraints through the `Desiderata` for a new revision, 
- The Rota Maker (delegated role for solving the planning issues) have a way to import the shifts (see below), and lightly edit them, 
- Once a future planning is available for preview, each user has a dedicated view.


### Import shifts from the CSV file (for RotaMakers)
If one provides a csv file (example below) 
that has start date in the file name, ie. ```some_name_ASOF__YYYY-MM-DD.csv ```
all shifts will be imported automatically.

```buildoutcfg
# name, day1, day2, day3, day4, day5, day6, day7 ....
name1, NWH, NWH, , , , , ,
name2, , , NWH, NWH,
```

> **Shift roles assignment:**
> - there may be a default shift-role assignment per import,
> - if the default is not assigned, the member roles will be used,
> - if the default should not be used ```@@``` tag should be used, e.g. ```AM:@@```, it will make use of member assigned role,
> - if different shift role should be used, mark it explicitly ```AM:TS2S```.
> 
>**Note**:
> - spaces between the comas are removed
> - if the shift is not found, the import default one is assigned.

>**IMPORTANT**:
>names and shift-day-slots need to be defined in the system.  
> In case name/slot is not found, given name-day-slot is skipped!


#### Available slots and roles
The initial import (see the later part of the installation part) provides the following shift slots:
```buildoutcfg
AM - morning
PM - afternoon
NWH - normal working hours
```
and member roles:
```buildoutcfg
SL - Shift Leader
OP - Operator
SE - System Expert
STL - Study Leader
LM - Line Manager
```