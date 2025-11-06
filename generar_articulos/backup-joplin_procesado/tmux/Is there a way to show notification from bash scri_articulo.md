<think>
Okay, so I need to figure out how to show notifications from a bash script in Ubuntu. I've heard that notify-send is a tool for this, but I'm not exactly sure how it works. Let me start by understanding what notify-send does.

From what I remember, notify-send sends desktop notifications. That means when I run a script, it can pop up a message on the screen without needing any extra software beyond what's already installed in Ubuntu. Cool, that sounds useful for automating tasks and getting feedback without interrupting the user too much.

I think the basic command is something like `notify-send "title" "message"`. But I also saw an example with some options. Let me check that again. Oh right, there was a command: `notify-send --expire-time=0 "Hello World"`. So this shows a notification with "Hello World" as both the title and message, but wait—no, maybe it's just the message. I should clarify how the title works.

Wait, actually, when you run `notify-send`, the first argument is the title, and the second is the body. So in that example, "Hello World" would be the title, but there was no body specified, so perhaps it only shows the title? Or maybe the body defaults to empty if not provided. Hmm.

Looking at the options, I see -u or --urgency for levels like low, normal, critical. That could change how urgent the notification appears. Then there's -t or --expire-time which sets how long the notification stays before disappearing. The example used 0, so it probably means it never expires unless the user clicks it.

Another option is -i or --icon, which allows adding an icon. I think you can specify a filename of an image or use a stock icon like 'info' or something. That could make notifications more visually informative.

And then there's -c or --category to set the notification category, which might help in organizing or filtering notifications in the system.

Putting this all together, I should be able to create simple scripts that notify me when a process finishes or alert me about certain events without cluttering my screen. For example, after backing up files, a script could pop up a message saying "Backup completed successfully."

I wonder how to test this. Maybe I'll open a terminal and type `notify-send --help` to see all the options again. Then try some commands:

- Just sending a basic notification: `notify-send "Hello" "World"`
- Adding an icon: I need to find or create an image file, say icon.png, then use `notify-send -i icon.png "Icon Test" "Message with icon"`
- Testing urgency levels: `notify-send --urgency=critical "Urgent!" "Something needs attention"`
- Setting an expiration time: Maybe 5000ms is 5 seconds. So `notify-send -t 5000 "Timer" "This will disappear after 5 seconds"`

I should also check if there are any dependencies or if notify-send comes by default in Ubuntu. From what I know, it's part of the desktop environment, so as long as I'm using a DE like Unity or GNOME, it should work.

Potential issues: What if the user isn't logged in interactively? Would notifications still show up when running scripts from cron? Probably not, because cron doesn't have a display. So maybe this is better for scripts run manually or within a desktop session.

Also, some applications might ignore notifications based on settings, so I should consider that my notification might be blocked by the user's system settings. But for most cases, it should work fine.

In summary, notify-send is a powerful tool for adding notifications to bash scripts in Ubuntu, allowing me to enhance automation with visual feedback.
</think>

# How to Show Notifications from a Bash Script in Ubuntu Using notify-send

**Introduction**

Notifications are a great way to provide feedback without interrupting the user. In Ubuntu, you can easily display desktop notifications directly from a bash script using `notify-send`. This tool allows you to send notifications that appear in the system's notification area, making your scripts more interactive and user-friendly.

## Getting Started

To begin, ensure that `notify-send` is installed on your system. It typically comes pre-installed with most Ubuntu desktop environments like Unity or GNOME. If it's not available, you might need to install it using:

```bash
sudo apt-get install libnotify-bin
```

**Basic Usage**

The simplest way to display a notification is by using the following command in your script:

```bash
notify-send "Hello World"
```

This will show a notification with the title "Hello" and the message "World". If you want both the title and message to be "Hello World", you can include it as two separate arguments.

**Customizing Notifications**

You can enhance notifications by adding optional parameters:

- **Urgency Levels**: Change how urgent a notification appears using `--urgency`. Possible values are `low`, `normal`, or `critical`.

  ```bash
  notify-send --urgency=critical "Critical Alert" "Immediate attention needed!"
  ```

- **Expiration Time**: Set how long the notification stays before disappearing with `--expire-time` in milliseconds.

  ```bash
  notify-send --expire-time=5000 "Timer Notification" "This will disappear after 5 seconds."
  ```

- **Icons**: Add visual cues by including an icon. You can use existing icons or custom images.

  ```bash
  notify-send -i /path/to/image.png "Icon Example" "Notification with an image"
  ```

- **Categories**: Organize notifications into categories for better management.

  ```bash
  notify-send --category=system "System Message" "A new system update is available."
  ```

**Practical Applications**

Here are some real-world examples of how to use `notify-send`:

1. **Backup Completion Notification**

   Add this command after your backup script runs:

   ```bash
   notify-send "Backup Complete" "Your files have been successfully backed up."
   ```

2. **Scheduled Task Reminder**

   Use a cron job to run a script that reminds you of an upcoming task:

   ```bash
   notify-send --urgency=low --expire-time=360000 "Reminder" "Don't forget your appointment at 2 PM."
   ```

3. **Download Completion Alert**

   Trigger this command after a download completes to alert the user.

   ```bash
   notify-send -i /usr/share/icons/ubuntu-logo.png "Download Finished" "Your file has been downloaded successfully."
   ```

**Troubleshooting and Best Practices**

- **Testing**: Always test your notifications in an interactive session before integrating them into automated scripts.
  
- **Cron Jobs**: Notifications might not display when run from cron because they require a graphical environment. Consider using tools like `dbus-send` or ensure your script runs within a desktop session.

- **User Settings**: Be mindful that users can configure their system to ignore or block notifications, which could affect how your scripts behave.

**Conclusion**

By incorporating `notify-send` into your bash scripts, you can elevate your automation tasks by providing clear and timely feedback. Whether it's confirming task completion or alerting the user to important events, notifications make scripts more engaging and effective.