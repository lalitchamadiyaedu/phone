package com.example.mdm

import android.app.admin.DeviceAdminReceiver
import android.content.Context
import android.content.Intent
import android.widget.Toast

class MyDeviceAdminReceiver : DeviceAdminReceiver() {

    override fun onEnabled(context: Context, intent: Intent) {
        super.onEnabled(context, intent)
        Toast.makeText(context, "Enterprise Device Admin Activated", Toast.LENGTH_SHORT).show()
    }

    override fun onDisabled(context: Context, intent: Intent) {
        super.onDisabled(context, intent)
        Toast.makeText(context, "Enterprise Device Admin Deactivated", Toast.LENGTH_SHORT).show()
    }

    override fun onPasswordFailed(context: Context, intent: Intent) {
        super.onPasswordFailed(context, intent)
        Toast.makeText(context, "Security Alert: Failed Unlock Attempt", Toast.LENGTH_SHORT).show()
    }

    override fun onPasswordSucceeded(context: Context, intent: Intent) {
        super.onPasswordSucceeded(context, intent)
        Toast.makeText(context, "Unlock Succeeded", Toast.LENGTH_SHORT).show()
    }
}
