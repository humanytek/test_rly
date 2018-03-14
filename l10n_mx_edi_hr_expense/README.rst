Mexican Expenses
================

This module allows to generate a supplier invoice (vendor bill) from an expense
which has an XML file related in your documents.

When an expense is approved, if it contains an XML file in their attachments,
the system tries to generate a new supplier invoice based on the CFDI, automatically filling
automatically some fields.

**What are the steps?**


- Create an expense for an employee who has already configured an associated
  journal (see the Configuration section for more information about how
  journals should be set up). Pay special attention to the field `Payment By`
  because the behavior will vary depending on whether the employee needs to
  be reimbursed.

    .. image:: l10n_mx_edi_hr_expense/static/src/img/step1.png
      :width: 400pt
      :alt: Creating an expense

- Attach an XML file corresponding to the CFDI.

    .. image:: l10n_mx_edi_hr_expense/static/src/img/step2.png
      :width: 400pt
      :alt: Attaching a CFDI

- Submit the expense to manager

    .. image:: l10n_mx_edi_hr_expense/static/src/img/step3.png
      :width: 400pt
      :alt: Submitting expense to manager

- Approve the expense, this task is done by the manager. If the CFDI attached
  is all right, a new supplier invoice is created using the information of the
  CFDI. You may look at the messages to ensure the invoice was created
  correctly. If any error occurs, please check the section
  `Posible errors in the invoice creation` to know about most common causes.

    .. image:: l10n_mx_edi_hr_expense/static/src/img/step4.png
      :width: 400pt
      :alt: Message list

- Once the manager has approved the expense, the invoice is automatically
  created. To check the newly created invoice, click on the button `Invoices`.

    .. image:: l10n_mx_edi_hr_expense/static/src/img/step5.png
      :width: 400pt
      :alt: Created invoices

- At this point, the behavior will depend on what the field `Payment By` was
  filled with: `Employee (to reimburse)` or `Company`. In other words, it will
  depend on wheter the payment method used to pay the expense belongs to the
  employee or belongs to the company.

    - If the payment method belongs to the company, then the invoice is created
      in draft mode. No additional steps are required, because the invoice is
      created as a regular supplier invoice and may be treated as such.

      .. image:: l10n_mx_edi_hr_expense/static/src/img/step6a.png
        :width: 400pt
        :alt: Created invoice, payment by company

    - If the payment method belongs to the employee, the invoice is created and
      validated; and then is automatically paid registering a new payment from
      the employee's journal.

      .. image:: l10n_mx_edi_hr_expense/static/src/img/step6b.png
        :width: 400pt
        :alt: Created invoice, payment by employee

- Since the employee has to be reimbursed, then the journal assigned to the
  employee will have a negative amount, which represents the exact amount the
  company owes to that employee.

    .. image:: l10n_mx_edi_hr_expense/static/src/img/step7.png
      :width: 400pt
      :alt: Negative valance

- The employee is reimbursed as a petty cash replenishment, i.e. with an
  internal transfer from one of the company's accounts. To do so, click on 
  `More` -> `Internal Transfer` -> `Create`

    .. image:: l10n_mx_edi_hr_expense/static/src/img/step8.png
      :width: 400pt
      :alt: Creating transfer to reimburse

- Finally, make a transfer from one of the company's accounts to the
  employee's journal and click `Confirm`. After doing so, the valance of the
  employee's journal should go to Cero

    .. image:: l10n_mx_edi_hr_expense/static/src/img/step9.png
      :width: 400pt
      :alt: Valance cero

  *Considerations:*

  - If the product in the CFDI is not found in the system when the invoice
    is created, it will be taken from the product assigned in the expense.

**Posible errors in the invoice creation**

- *The Receptor's RFC in the XML does not match with your Company's RFC*

  This error is produced when the Receiver's VAT in the CFDI is different from
  the VAT assigned in the company. The document is incorrect, because it menas
  it does not belong to your company.

- *The XML UUID belongs to other invoice.*

  This error is produced when another invoice with the same UUID is found,
  because UUIDs are  unique, which means the invoice is duplicated.

- *The invoice reference belongs to other invoice of the same partner.*

  Each invoice has a `Vendor Reference`. This field is filled when the invoice
  is created, but there should not be two invoices created with the same value.

Installation
============

  - Download this module from `Vauxoo/mexico
    <https://github.com/vauxoo/mexico>`_
  - Add the repository folder into your odoo addons-path.
  - Go to ``Settings > Module list``, search for the current name and click in
    ``Install`` button.

Configuration
=============

Since this module addresses employees's reimbursements as petty cash
replenishments, it requires a journal for each employee who makes expenses.
Those journals must be configured as follows:

- `Journal Name`: This should be a representative name that identifies the
  employee, e.g. Expenses of John Doe
- `Type`: `Cash` or `Bank`, accordingly
- `Default debit account`: The wage account which the employee is paid from.
- `Default Credit Account`: Same as `Default Debit Account`

  .. image:: l10n_mx_edi_hr_expense/static/src/img/config1.png
    :width: 400pt
    :alt: Journal configuration

Then, edit the involved employee, and under the tab `Public Information`, set the field `Journal` with the journal just created.

  .. image:: l10n_mx_edi_hr_expense/static/src/img/config2.png
    :width: 400pt
    :alt: Employee configuration

Tip: if there are too many journals on the dashboard, they may be hidden
following one of these equivalent alternatives:

- On the accounting dashboard, locate the journal you'd like to hide, click the
  `More` button and unmark the option `Favorite`.

  .. image:: l10n_mx_edi_hr_expense/static/src/img/tip1.png
    :width: 400pt
    :alt: Hiding a journal, option 1

- When creating a new journal, uncheck the option `Show journal on dashboard`,
  located in the `Advanced options` tab.

  .. image:: l10n_mx_edi_hr_expense/static/src/img/tip2.png
    :width: 400pt
    :alt: Hiding a journal, option 2

  **Note**: the Debug mode must be enabled for that option to show up.

Bug Tracker
===========

Bugs are tracked on
`GitHub Issues <https://github.com/Vauxoo/mexico/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and
welcomed feedback
`here <https://github.com/Vauxoo/mexico/issues/new?body=module:%20
l10n_mx_bedi_hr_expense%0Aversion:%20
10.0.1.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_

Credits
=======

**Contributors**

* Nhomar Hernández <nhomar@vauxoo.com> (Planner/Auditor)
* Luis Torres <luis_t@vauxoo.com> (Developer)

Maintainer
==========

.. image:: https://s3.amazonaws.com/s3.vauxoo.com/description_logo.png
   :alt: Vauxoo
