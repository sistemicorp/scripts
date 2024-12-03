Travellers
##########

Travellers are 2D bar codes printed on paper than can configure Prism
to run a script with certain substitution parameters.

Travellers are used to simplify setting up and operating Prism by any
User (operator) that may not be familiar with the production process.

Travellers can only be created by users with the :ref:`prism_accounts:ConfigMan` role.

The image below shows the `Test Config` view, a script has been selected and
the parameters selected, at this point the `Traveller` button turns Green
indicating it can now be pressed.

.. image:: static/Screenshot_traveller_01.png


Pressing the `Traveller` button will pop up a new tab in the browser, similiar
to the following,

.. image:: static/Screenshot_traveller_02.png

The traveller shows the User that created it, the time and date, and the parameters
used when it was created.

This is a PDF document.
Use the browser functions to either Print or Save this document and pass
it along to the production floor.

Scanning
********

Travellers are scanned by the operator using most any bar code scanner set
to emulate the keyboard.

.. image:: static/Screenshot_traveller_03.png

Once the image is scanned, you `Apply`, `Submit` and the `Test` to proceed
to the Test View.

User Content
************

Adding a `traveller` section to the script you may add your own content.
For example see `public/prism/scripts/example/prod_v0/prod_0.scr`,

::

    {
      "info": { ... },
      "config": { ... },
      "tests": [ ... ],
      "traveller": {
        // text to appear in a cell on the Traveller PDF
        // must be one line (per cell), use \n for newlines
        "Instructions": "1. On Your Mark.\n2. Get Set.\n3. Go!",
        "Inspections": "QA: ______________          COUNT IN: ___________ PASS: ___________ FAIL: ____________\nMFG:____________"
      }
    }
