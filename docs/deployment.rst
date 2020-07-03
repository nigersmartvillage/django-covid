==============
AWS Deployment
==============

The Covid Library can be deployed as a cloned instance by using
the open source Django project with any deployment strategy or
by starting with a pre-packaged community machine image (AMI) for
running on Amazon Web Services.

Quickstart deployment to AWS
============================

The codebase includes a CloudFormation template, `cloudformation.yml`,
which can be uploaded as-is to the AWS CloudFormation service and
used to create an entire stack including EC2 instance, VPC, security
groups, and internet gateway.

1. Log into your AWS console
2. Access the CloudFormation console: https://console.aws.amazon.com/cloudformation/home
3. Click the "Create stack" button and then select "With new resources"
4. Ensure "Template is ready" is selected and then choose "Upload a template file"
5. Find the `cloudformation.yml` file on your computer and select it
6. Follow the subsequent dialog forms and then wait for your stack to finalize.

You will need to select a keypair to install for access. The remaining
items can be completed manually or in some cases with some help from
the Ansible tasks herein.

.. important::
   The Ansible tasks assume you have configured a host named `covid-library`
   (e.g. in `/ssh/config` on Linux or macOS) that specifies the host address,
   username (`ubuntu`), and path to the identify file you used to create
   your stack. You may reconfigure this as you want, but in order to work out
   of the box it is recommend you start by configuring a named `covid-library`
   host.

In the "Outputs" tab of the completed CloudFormation stack you can find the
IP address to your instance.

Direct AMI initialization
=========================

If you already have your own VPC established you can simply start an instance
from the Amazon EC2 AMI, which has ID of `ami-0c090dc979740a94b`.

Updating your installation
==========================

Prerequisites:

1. You have a recent version of Ansible installed.
2. Your instance is already installed remotely and accessible over SSH.
3. You have a remote SSH host configured with the name "covid-library" with
   host name, user, and identify file preconfigured. This is not strictly
   required however without it you will need to adapt the hosts information.

Installation Steps
------------------

These steps will complete installation so your site is available over HTTPS
and your custom domain.

1. Add a `custom.yml` file in `deployment/vars`. This is where you will
   keep custom variables, e.g. the host name of your site.
2. Run the `aws.sh` script with the extra flag `--check` - this will be passed
   through to the Ansible playbook program and ensures that it runs without
   doing anything at first, just showing what it *would* do if it ran
3. Now run the script without the `--check` flag.

If this ran successfully your site should now be accessible over HTTPS from your
custom domain.

Subsequent updates and working with the deployment
==================================================

The root of the deployed directory is `/home/www/platform`. Unless you change your `~/.bashrc`
file, this will be your working directory when you log into the instance. You will
also have the library's Python 3.6 virtual environment activated immediately. This
has the effect of changing the Python path and aligning it with the web application's
isolated virtualenvironment.

To access the Django app, change into `django-covid`.

    cd django-covid

The first thing you should assess and modify is the `local_settings.py` file which is
located in `config/local_settings.py`, the full path is `/home/www/platform/django-covid/config/local_settings.py`.
This file is not source controlled and is *imported* by the Django application's primary
source controlled settings. By doing so it may override the base settings or add to them.

You should go through this file and address the items commented for your attention, including
the Django "secret key" (you can change to arbitrarily random text), various email addresses,
and the allowed host names.
