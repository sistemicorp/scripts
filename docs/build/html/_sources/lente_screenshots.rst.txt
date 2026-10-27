Screenshots
###########

Lente screenshots.

The left menu has `Home`, `Station Manager`, `Result Search`, `Result Analytics`, `Create Traveller`, and under
`Admin`, `Account Management`, `Shutdown` and `Send Logs`.  Any logged in user can open `Result Search` and
`Result Analytics`.  `Create Traveller` needs the Admin, ConfigMan or Developer role, the other pages need Admin.

`Result Search` shows the same filters and results table as `Result Analytics`, without the charts.
Both pages have an `Export CSV` button, and a `Copy SQL Hint` button which copies the SQL query behind the table.

Home
****

Before login, Home shows the license operator and the Lente host name and IP.

After login, Home is a summary of the production line.
The top chart shows the throughput and yield of all stations over the last `Days` (1 to 30), in hourly bars
for up to 2 days and daily bars after that.  It refreshes every minute.

Below the chart is the stations table, with each station's health, running script, users and last ping.

Result Analytics
****************

The Result Analytics dashboard is for detailed results analysis.  Results shown graphically and in
the table are filtered by the current state of the "Select/Date" filters.

If a date filter is not valid, or the results database cannot be read, the table shows
`Results Data not valid` and the charts are emptied.

The dashboard has three views, selected by the tabs across the top,

* `Throughput & Yield` - history of Pass/Fail/Yield numbers
* `Failure Pareto` - which tests are failing, ranked by how often
* `Test Runtime` - where the test time is being spent

The `Results Summary` panel on the right totals the Pass/Fail/Yield for the current filter selection.

The table below the filters is each result.  By selecting a result in this table, a new tab is opened with the
result details.

The `Throughput & Yield` tab charts the units tested over time; Pass and Fail as stacked bars against the left
axis, and Yield as a line against the right axis.  The period selector sets the size of each bar, for
example `Daily`.  Use this to track production output and yield trend.
A period with no results has no yield, and the Yield line has a gap there.

Select `Lot` in the period selector to get one bar per lot instead, ordered by the date each lot was first
tested.  Results without a lot are grouped as `(none)`.  Use the date and `Lot` filters to limit which lots
are shown.

The count selector sets what is counted.  `All results` counts every test result, so a unit tested twice
counts twice.  The unique choices count each unit once, where a unit is the `product` and `key0`, for example
a serial number.  Results without a `key0` each count as one.

* `Unique units, last result` - each unit's latest result, the final yield.  A unit that failed, was
  repaired and passed counts as one pass.
* `Unique units, first result` - each unit's first result, the first pass yield.

A unit is counted in the period or lot of the result chosen for it.  To use the unique counts, scripts
must save the unit's serial number in `key0`, see :ref:`_database:record`.

.. image:: static/Screenshot_lente_throughput.png

The `Failure Pareto` tab ranks the failing tests by quantity, and shows each as a percentage of the failed runs
and of all runs.  Use this to find which tests are costing you the most yield.

.. image:: static/Screenshot_lente_pareto.png

The `Test Runtime` tab breaks down where the test time is being spent.  Select the `Script` and the `Script Result`
to report on.  The table gives the average time of each test item and its percentage of the total, and the pie
chart shows the same proportions.  Use this to find which test items to optimize to reduce cycle time.

.. image:: static/Screenshot_lente_runtime.png


Station Manager
***************

Prism and Lente Station management console, Admin only.

* View station stats - version, scripts, backups, disk usage, the script running, the test runner
  state, active users, and last ping
* Select stations and take actions - `Ping`, `Get Log`, `Restart`, `Sync Users`, `Sync Script`

  * Lente never connects to a station.  An action is sent in the reply to the station's next
    ping, about every 20 seconds, so stations behind a firewall or NAT can be managed.  The `Cmd`
    column shows the action as `pending`, then `sent`.  An action not picked up within 2 minutes
    is dropped and shown as `expired`.
  * `Sync Users` sends the users that have the ServerSync role
  * `Sync Users` and `Sync Script` are disabled while a user is logged in to the selected station,
    or while its test runner has a script loaded (`Runner` is `IDLE` or `RUNNING`).  Prism also
    refuses these syncs while a script is loaded, and refuses `Sync Script` while a user is logged in,
    because installing scripts restarts Prism.  Log out on the station to allow them, logging out
    exits the Script Runner.
  * `Restart` asks for confirmation when a selected station has a user logged in or a script
    loaded, because restarting aborts any running tests.  Restart stays available to recover a
    station that is not responding.
  * with `"auto_sync_scripts": true` in :ref:`settings.json <deploy-settings-file>`, Lente syncs
    scripts to stations automatically when the scripts version changes, no user is logged in,
    and the station's test runner has no script loaded.  If a user logs in before the sync starts,
    it waits and runs after they log out.

* `git pull` (shown only on the root Lente, `"root_authority": true`) updates the Lente scripts from
  GitHub.  It requires `public/git_pull_watcher.sh` to be running on the Lente host, see
  :ref:`Lente Git Pull <lente-git-pull>`.
* `Offline Stations` lists every station that has pinged this Lente but is not pinging now, with its
  last version, IP and when it was last seen.  Stations from downstream Lentes are included.
  The list is kept in `public/stations.sqlite`, so it survives a Lente restart.  A station moves
  back to the live list when it pings again.

  * `Remove` and `Remove All` permanently delete offline stations from the list, for stations
    that are no longer in service.  A removed station that pings again is added back.

* `Station Logs` below lists station events, filtered by the Type/Computer/Version/Cause and date selections

  * click `Station Logs` to open or close the list.  It starts closed, and the page remembers
    your choice

.. image:: static/Screenshot_lente_station_mgr.png


Account Management
******************

A single page manages all of the Account Management features.

The table at the top summarizes the Users; their email, whether they are Active, their Language, and their Roles.

* `New Account` creates a User
* Selecting a User in the table loads them into the editor below

The editor sets the User's Language, whether the account is `Active`, and which Roles they hold.  `Set Password`
sets the User's password.  `Update` saves the changes, `Reset` discards them, and `Delete` removes the User.

.. image:: static/Screenshot_lente_acct_mgt.png