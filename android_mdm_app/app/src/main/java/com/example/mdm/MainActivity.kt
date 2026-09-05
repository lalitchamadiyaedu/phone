package com.example.mdm

import android.Manifest
import android.app.Activity
import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

class MainActivity : AppCompatActivity() {

    private lateinit var devicePolicyManager: DevicePolicyManager
    private lateinit var adminComponent: ComponentName

    private lateinit var tvAdminStatus: TextView
    private lateinit var tvSecurityStatus: TextView
    private lateinit var etPhoneNumber: EditText
    private lateinit var etServerHost: EditText
    private lateinit var btnRegisterAsset: Button
    private lateinit var btnToggleAdmin: Button
    private lateinit var btnRequestPermissions: Button
    private lateinit var btnEnforcePolicy: Button
    private lateinit var btnLockScreen: Button

    companion object {
        private const val REQUEST_CODE_ENABLE_ADMIN = 1001
        private const val REQUEST_CODE_PERMISSIONS = 1002

        private val REQUIRED_PERMISSIONS = arrayOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION,
            Manifest.permission.READ_PHONE_STATE
        )
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Dynamic UI Layout
        val layout = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            setPadding(48, 48, 48, 48)
            setBackgroundColor(0xFF0F172A.toInt())
        }

        tvAdminStatus = TextView(this).apply {
            textSize = 18f
            setTextColor(0xFFFFFFFF.toInt())
            setPadding(0, 0, 0, 16)
        }
        layout.addView(tvAdminStatus)

        tvSecurityStatus = TextView(this).apply {
            textSize = 14f
            setTextColor(0xFF94A3B8.toInt())
            setPadding(0, 0, 0, 24)
        }
        layout.addView(tvSecurityStatus)

        etServerHost = EditText(this).apply {
            hint = "Server Host URL (e.g. http://10.0.2.2:8000)"
            setText("http://10.0.2.2:8000")
            setTextColor(0xFFFFFFFF.toInt())
            setHintTextColor(0xFF64748B.toInt())
            setPadding(24, 24, 24, 24)
        }
        layout.addView(etServerHost)

        etPhoneNumber = EditText(this).apply {
            hint = "Corporate Phone Number / Asset ID"
            setTextColor(0xFFFFFFFF.toInt())
            setHintTextColor(0xFF64748B.toInt())
            setPadding(24, 24, 24, 24)
        }
        layout.addView(etPhoneNumber)

        btnRegisterAsset = Button(this).apply {
            text = "Register Enterprise Device Asset"
            setOnClickListener { registerEnterpriseAsset() }
        }
        layout.addView(btnRegisterAsset)

        btnRequestPermissions = Button(this).apply {
            text = "Request All Runtime Permissions"
            setOnClickListener { checkAndRequestPermissions() }
        }
        layout.addView(btnRequestPermissions)

        btnToggleAdmin = Button(this).apply {
            text = "Enable Device Administrator"
            setOnClickListener { toggleDeviceAdmin() }
        }
        layout.addView(btnToggleAdmin)

        btnEnforcePolicy = Button(this).apply {
            text = "Enforce Security Password Policy"
            setOnClickListener { enforceSecurityPolicy() }
        }
        layout.addView(btnEnforcePolicy)

        btnLockScreen = Button(this).apply {
            text = "Lock Device Screen"
            setOnClickListener { lockDeviceNow() }
        }
        layout.addView(btnLockScreen)

        setContentView(layout)

        // Initialize DevicePolicyManager & Admin Component
        devicePolicyManager = getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
        adminComponent = ComponentName(this, MyDeviceAdminReceiver::class.java)

        checkAndRequestPermissions()
        updateAdminStatusUI()
    }

    override fun onResume() {
        super.onResume()
        updateAdminStatusUI()
    }

    private fun checkAndRequestPermissions() {
        val missingPermissions = REQUIRED_PERMISSIONS.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (missingPermissions.isNotEmpty()) {
            ActivityCompat.requestPermissions(
                this,
                missingPermissions.toTypedArray(),
                REQUEST_CODE_PERMISSIONS
            )
        }
    }

    private fun updateAdminStatusUI() {
        val isAdminActive = devicePolicyManager.isAdminActive(adminComponent)
        val missingPermissions = REQUIRED_PERMISSIONS.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        val permStatus = if (missingPermissions.isEmpty()) "ALL GRANTED" else "MISSING (${missingPermissions.size})"

        if (isAdminActive) {
            tvAdminStatus.text = "● STATUS: DEVICE ADMIN ACTIVE"
            tvAdminStatus.setTextColor(0xFF34D399.toInt())
            btnToggleAdmin.text = "Deactivate Device Admin"

            val isPassSufficient = devicePolicyManager.isActivePasswordSufficient
            tvSecurityStatus.text = "Permissions: $permStatus\nPassword Compliance: ${if (isPassSufficient) "COMPLIANT" else "NON-COMPLIANT"}"
        } else {
            tvAdminStatus.text = "● STATUS: INACTIVE"
            tvAdminStatus.setTextColor(0xFFF87171.toInt())
            btnToggleAdmin.text = "Activate Device Admin"
            tvSecurityStatus.text = "Permissions: $permStatus\nDevice Administrator privileges required to inspect policies."
        }
    }

    private fun registerEnterpriseAsset() {
        val phoneNum = etPhoneNumber.text.toString().trim()
        val serverHost = etServerHost.text.toString().trim()

        if (phoneNum.isEmpty()) {
            Toast.makeText(this, "Please enter a phone number / asset ID", Toast.LENGTH_SHORT).show()
            return
        }

        val isAdminActive = devicePolicyManager.isAdminActive(adminComponent)
        val isPassSufficient = devicePolicyManager.isActivePasswordSufficient
        val deviceModel = "${Build.MANUFACTURER} ${Build.MODEL}"
        val osInfo = "Android ${Build.VERSION.RELEASE} (SDK ${Build.VERSION.SDK_INT})"

        thread {
            try {
                val url = URL("$serverHost/api/register-asset/")
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                conn.doOutput = true

                val json = JSONObject().apply {
                    put("phone_number", phoneNum)
                    put("device_model", deviceModel)
                    put("os_info", osInfo)
                    put("admin_active", isAdminActive)
                    put("password_compliant", isPassSufficient)
                }

                val writer = OutputStreamWriter(conn.outputStream)
                writer.write(json.toString())
                writer.flush()
                writer.close()

                val respCode = conn.responseCode
                if (respCode == 200) {
                    runOnUiThread {
                        Toast.makeText(this, "Asset Registered Successfully on Dashboard!", Toast.LENGTH_LONG).show()
                    }
                } else {
                    runOnUiThread {
                        Toast.makeText(this, "Registration failed. Response Code: $respCode", Toast.LENGTH_SHORT).show()
                    }
                }
            } catch (e: Exception) {
                runOnUiThread {
                    Toast.makeText(this, "Error connecting to server: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    private fun toggleDeviceAdmin() {
        val isAdminActive = devicePolicyManager.isAdminActive(adminComponent)
        if (!isAdminActive) {
            val intent = Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN).apply {
                putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, adminComponent)
                putExtra(
                    DevicePolicyManager.EXTRA_ADD_EXPLANATION,
                    "Enterprise Policy Administrator requires permission to enforce security password compliance."
                )
            }
            startActivityForResult(intent, REQUEST_CODE_ENABLE_ADMIN)
        } else {
            devicePolicyManager.removeActiveAdmin(adminComponent)
            Toast.makeText(this, "Device Administrator privileges removed", Toast.LENGTH_SHORT).show()
            updateAdminStatusUI()
        }
    }

    private fun enforceSecurityPolicy() {
        if (!devicePolicyManager.isAdminActive(adminComponent)) {
            Toast.makeText(this, "Please activate Device Admin first", Toast.LENGTH_SHORT).show()
            return
        }

        try {
            devicePolicyManager.setPasswordQuality(
                adminComponent,
                DevicePolicyManager.PASSWORD_QUALITY_NUMERIC
            )
            devicePolicyManager.setPasswordMinimumLength(adminComponent, 6)

            Toast.makeText(this, "Security Policy Enforced: Min 6-digit PIN required", Toast.LENGTH_LONG).show()
            updateAdminStatusUI()
        } catch (e: Exception) {
            Toast.makeText(this, "Error enforcing policy: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }

    private fun lockDeviceNow() {
        if (!devicePolicyManager.isAdminActive(adminComponent)) {
            Toast.makeText(this, "Please activate Device Admin first", Toast.LENGTH_SHORT).show()
            return
        }
        devicePolicyManager.lockNow()
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_CODE_PERMISSIONS) {
            val allGranted = grantResults.all { it == PackageManager.PERMISSION_GRANTED }
            if (allGranted) {
                Toast.makeText(this, "Runtime Permissions Granted!", Toast.LENGTH_SHORT).show()
            }
            updateAdminStatusUI()
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_CODE_ENABLE_ADMIN) {
            if (resultCode == Activity.RESULT_OK) {
                Toast.makeText(this, "Device Admin Activated Successfully!", Toast.LENGTH_SHORT).show()
            }
            updateAdminStatusUI()
        }
    }
}
