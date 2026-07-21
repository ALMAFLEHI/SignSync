package com.example.flutter_app

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Matrix
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.util.Size
import android.view.View
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import androidx.lifecycle.LifecycleOwner
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarker
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarkerResult
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import io.flutter.plugin.common.StandardMessageCodec
import io.flutter.plugin.platform.PlatformView
import io.flutter.plugin.platform.PlatformViewFactory
import java.io.File
import java.util.Locale
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

class MainActivity : FlutterActivity() {
    private val liveCameraBridge = LiveCameraBridge()

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        val channel = MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            LiveCameraBridge.CHANNEL_NAME
        )
        liveCameraBridge.attach(this, channel)
        channel.setMethodCallHandler { call, result ->
            liveCameraBridge.handleMethod(call, result)
        }

        flutterEngine
            .platformViewsController
            .registry
            .registerViewFactory(
                LiveCameraBridge.VIEW_TYPE,
                LiveCameraViewFactory(liveCameraBridge)
            )
    }

    override fun onDestroy() {
        liveCameraBridge.dispose()
        super.onDestroy()
    }
}

private class LiveCameraViewFactory(
    private val bridge: LiveCameraBridge
) : PlatformViewFactory(StandardMessageCodec.INSTANCE) {
    override fun create(context: Context, viewId: Int, args: Any?): PlatformView {
        return LiveCameraPlatformView(context, bridge)
    }
}

private class LiveCameraPlatformView(
    context: Context,
    private val bridge: LiveCameraBridge
) : PlatformView {
    private val previewView: PreviewView = bridge.ensurePreviewView(context)

    override fun getView(): View = previewView

    override fun dispose() = Unit
}

private class LiveCameraBridge {
    companion object {
        const val CHANNEL_NAME = "signsync/live_landmarks"
        const val VIEW_TYPE = "signsync/live_camera_view"
        private const val HAND_LANDMARKER_ASSET = "hand_landmarker.task"
        private const val FRAME_WIDTH = 126
        private const val HAND_WIDTH = 63
    }

    private val mainHandler = Handler(Looper.getMainLooper())
    private val cameraExecutor: ExecutorService = Executors.newSingleThreadExecutor()
    private val isProcessingFrame = AtomicBoolean(false)

    private var activity: Activity? = null
    private var channel: MethodChannel? = null
    private var previewView: PreviewView? = null
    private var cameraProvider: ProcessCameraProvider? = null
    private var handLandmarker: HandLandmarker? = null
    private var cameraStarted = false

    fun attach(activity: Activity, channel: MethodChannel) {
        this.activity = activity
        this.channel = channel
    }

    fun ensurePreviewView(context: Context): PreviewView {
        val existing = previewView
        if (existing != null) {
            return existing
        }

        val created = PreviewView(context).apply {
            implementationMode = PreviewView.ImplementationMode.COMPATIBLE
            scaleType = PreviewView.ScaleType.FILL_CENTER
        }
        previewView = created
        return created
    }

    fun handleMethod(call: MethodCall, result: MethodChannel.Result) {
        when (call.method) {
            "startCamera" -> startCamera(result)
            "stopCamera" -> {
                stopCamera()
                result.success(null)
            }
            "startCapture" -> {
                sendEvent("captureStarted", mapOf("message" to "Collecting valid landmark frames."))
                result.success(null)
            }
            "resetCapture" -> {
                sendEvent("captureReset", mapOf("message" to "Live landmark buffer reset."))
                result.success(null)
            }
            "getPhoneSampleDirectory" -> getPhoneSampleDirectory(result)
            "getEvaluationDirectory" -> getEvaluationDirectory(result)
            "getEvaluationDeviceInfo" -> getEvaluationDeviceInfo(result)
            else -> result.notImplemented()
        }
    }

    fun dispose() {
        stopCamera()
        handLandmarker?.close()
        handLandmarker = null
        cameraExecutor.shutdown()
        activity = null
        channel = null
        previewView = null
    }

    private fun startCamera(result: MethodChannel.Result) {
        val currentActivity = activity
        if (currentActivity == null) {
            result.error("activity_missing", "Android activity is not attached.", null)
            return
        }

        if (ContextCompat.checkSelfPermission(
                currentActivity,
                Manifest.permission.CAMERA
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            val message = "Camera permission is required for live landmark capture."
            sendEvent("cameraError", mapOf("message" to message))
            result.error("camera_permission_denied", message, null)
            return
        }

        try {
            initializeHandLandmarker(currentActivity)
        } catch (error: RuntimeException) {
            val message = error.message ?: "MediaPipe Hands initialization failed."
            sendEvent("mediapipeError", mapOf("message" to message))
            result.error("mediapipe_init_failed", message, error.toString())
            return
        }

        val providerFuture = ProcessCameraProvider.getInstance(currentActivity)
        providerFuture.addListener(
            {
                try {
                    val provider = providerFuture.get()
                    cameraProvider = provider
                    bindCameraUseCases(currentActivity, provider)
                    cameraStarted = true
                    sendEvent(
                        "cameraStarted",
                        mapOf("message" to "Camera started. MediaPipe Hands initialized.")
                    )
                    result.success(null)
                } catch (error: Exception) {
                    val message = error.message ?: "CameraX could not start."
                    sendEvent("cameraError", mapOf("message" to message))
                    result.error("camera_start_failed", message, error.toString())
                }
            },
            ContextCompat.getMainExecutor(currentActivity)
        )
    }

    private fun bindCameraUseCases(
        currentActivity: Activity,
        provider: ProcessCameraProvider
    ) {
        val lifecycleOwner = currentActivity as? LifecycleOwner
            ?: throw IllegalStateException("Flutter activity is not a LifecycleOwner.")
        val view = ensurePreviewView(currentActivity)

        val preview = Preview.Builder()
            .build()
            .also { it.setSurfaceProvider(view.surfaceProvider) }

        val analysis = ImageAnalysis.Builder()
            .setTargetResolution(Size(640, 480))
            .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
            .setOutputImageFormat(ImageAnalysis.OUTPUT_IMAGE_FORMAT_RGBA_8888)
            .build()
            .also {
                it.setAnalyzer(cameraExecutor) { imageProxy ->
                    analyzeImage(imageProxy)
                }
            }

        provider.unbindAll()
        provider.bindToLifecycle(
            lifecycleOwner,
            chooseCameraSelector(provider),
            preview,
            analysis
        )
    }

    private fun chooseCameraSelector(provider: ProcessCameraProvider): CameraSelector {
        return try {
            if (provider.hasCamera(CameraSelector.DEFAULT_FRONT_CAMERA)) {
                CameraSelector.DEFAULT_FRONT_CAMERA
            } else {
                CameraSelector.DEFAULT_BACK_CAMERA
            }
        } catch (_: Exception) {
            CameraSelector.DEFAULT_BACK_CAMERA
        }
    }

    private fun initializeHandLandmarker(context: Context) {
        if (handLandmarker != null) {
            return
        }

        val baseOptions = BaseOptions.builder()
            .setModelAssetPath(HAND_LANDMARKER_ASSET)
            .build()
        val options = HandLandmarker.HandLandmarkerOptions.builder()
            .setBaseOptions(baseOptions)
            .setRunningMode(RunningMode.LIVE_STREAM)
            .setNumHands(2)
            .setMinHandDetectionConfidence(0.5f)
            .setMinHandPresenceConfidence(0.5f)
            .setMinTrackingConfidence(0.5f)
            .setResultListener { result, _ ->
                isProcessingFrame.set(false)
                handleLandmarkerResult(result)
            }
            .setErrorListener { error ->
                isProcessingFrame.set(false)
                sendEvent(
                    "mediapipeError",
                    mapOf("message" to (error.message ?: error.toString()))
                )
            }
            .build()

        handLandmarker = HandLandmarker.createFromOptions(context, options)
    }

    private fun analyzeImage(imageProxy: ImageProxy) {
        val landmarker = handLandmarker
        if (!cameraStarted && cameraProvider == null) {
            imageProxy.close()
            return
        }
        if (landmarker == null) {
            imageProxy.close()
            return
        }
        if (isProcessingFrame.getAndSet(true)) {
            imageProxy.close()
            return
        }

        val timestampMs = SystemClock.uptimeMillis()
        val bitmap = imageProxyToBitmap(imageProxy)
        imageProxy.close()

        if (bitmap == null) {
            isProcessingFrame.set(false)
            sendEvent("cameraError", mapOf("message" to "Could not convert camera frame."))
            return
        }

        try {
            val mpImage = BitmapImageBuilder(bitmap).build()
            landmarker.detectAsync(mpImage, timestampMs)
        } catch (error: RuntimeException) {
            isProcessingFrame.set(false)
            sendEvent(
                "mediapipeError",
                mapOf("message" to (error.message ?: error.toString()))
            )
        }
    }

    private fun imageProxyToBitmap(imageProxy: ImageProxy): Bitmap? {
        return try {
            val plane = imageProxy.planes.firstOrNull() ?: return null
            val buffer = plane.buffer
            buffer.rewind()
            val bitmap = Bitmap.createBitmap(
                imageProxy.width,
                imageProxy.height,
                Bitmap.Config.ARGB_8888
            )
            bitmap.copyPixelsFromBuffer(buffer)
            rotateBitmap(bitmap, imageProxy.imageInfo.rotationDegrees)
        } catch (_: RuntimeException) {
            null
        }
    }

    private fun rotateBitmap(bitmap: Bitmap, rotationDegrees: Int): Bitmap {
        if (rotationDegrees == 0) {
            return bitmap
        }
        val matrix = Matrix().apply { postRotate(rotationDegrees.toFloat()) }
        val rotated = Bitmap.createBitmap(
            bitmap,
            0,
            0,
            bitmap.width,
            bitmap.height,
            matrix,
            true
        )
        if (rotated != bitmap) {
            bitmap.recycle()
        }
        return rotated
    }

    private fun handleLandmarkerResult(result: HandLandmarkerResult) {
        val detections = buildHandDetections(result)
        val frame = DoubleArray(FRAME_WIDTH)
        var leftDetected = false
        var rightDetected = false

        val used = mutableSetOf<HandDetection>()
        detections.forEach { detection ->
            when (detection.handedness) {
                "left" -> {
                    if (!leftDetected) {
                        copyHandToFrame(detection.values, frame, 0)
                        leftDetected = true
                        used.add(detection)
                    }
                }
                "right" -> {
                    if (!rightDetected) {
                        copyHandToFrame(detection.values, frame, 1)
                        rightDetected = true
                        used.add(detection)
                    }
                }
            }
        }

        detections
            .filterNot { used.contains(it) }
            .sortedBy { it.averageX }
            .forEach { detection ->
                if (!leftDetected) {
                    copyHandToFrame(detection.values, frame, 0)
                    leftDetected = true
                } else if (!rightDetected) {
                    copyHandToFrame(detection.values, frame, 1)
                    rightDetected = true
                }
            }

        sendEvent(
            "liveFrame",
            mapOf(
                "timestampMs" to result.timestampMs(),
                "handDetected" to detections.isNotEmpty(),
                "leftDetected" to leftDetected,
                "rightDetected" to rightDetected,
                "frameDimension" to if (detections.isNotEmpty()) FRAME_WIDTH else 0,
                "landmarks" to if (detections.isNotEmpty()) frame.toList() else emptyList<Double>()
            )
        )
    }

    private fun buildHandDetections(result: HandLandmarkerResult): List<HandDetection> {
        val handednesses = result.handednesses()
        return result.landmarks().mapIndexedNotNull { index, landmarks ->
            if (landmarks.size != 21) {
                return@mapIndexedNotNull null
            }

            val values = landmarks.flatMap { landmark ->
                listOf(
                    landmark.x().toDouble(),
                    landmark.y().toDouble(),
                    landmark.z().toDouble()
                )
            }
            if (values.size != HAND_WIDTH) {
                return@mapIndexedNotNull null
            }

            val averageX = landmarks.map { it.x().toDouble() }.average()
            val handedness = handednesses
                .getOrNull(index)
                ?.maxByOrNull { it.score() }
                ?.categoryName()
                ?.lowercase(Locale.US)
                ?: ""

            HandDetection(values, handedness, averageX)
        }
    }

    private fun copyHandToFrame(values: List<Double>, frame: DoubleArray, handSlot: Int) {
        val offset = handSlot * HAND_WIDTH
        values.take(HAND_WIDTH).forEachIndexed { index, value ->
            frame[offset + index] = value
        }
    }

    private fun stopCamera() {
        cameraProvider?.unbindAll()
        cameraStarted = false
        isProcessingFrame.set(false)
        sendEvent("cameraStopped", mapOf("message" to "Camera stopped."))
    }

    private fun sendEvent(method: String, payload: Map<String, Any>) {
        mainHandler.post {
            channel?.invokeMethod(method, payload)
        }
    }

    private fun getPhoneSampleDirectory(result: MethodChannel.Result) {
        val currentActivity = activity
        if (currentActivity == null) {
            result.error("activity_missing", "Android activity is not attached.", null)
            return
        }
        val baseDirectory = currentActivity.getExternalFilesDir(null)
        if (baseDirectory == null) {
            result.error("storage_missing", "Android external files directory is not available.", null)
            return
        }
        val sampleDirectory = File(baseDirectory, "signsync_phone_samples")
        if (!sampleDirectory.exists() && !sampleDirectory.mkdirs()) {
            result.error("storage_create_failed", "Could not create phone sample directory.", null)
            return
        }
        result.success(sampleDirectory.absolutePath)
    }

    private fun getEvaluationDirectory(result: MethodChannel.Result) {
        val currentActivity = activity
        if (currentActivity == null) {
            result.error("activity_missing", "Android activity is not attached.", null)
            return
        }
        val baseDirectory = currentActivity.getExternalFilesDir(null)
        if (baseDirectory == null) {
            result.error(
                "storage_missing",
                "Android external files directory is not available.",
                null
            )
            return
        }
        val evaluationDirectory = File(baseDirectory, "signsync_evaluation_sessions")
        if (!evaluationDirectory.exists() && !evaluationDirectory.mkdirs()) {
            result.error(
                "storage_create_failed",
                "Could not create evaluation session directory.",
                null
            )
            return
        }
        result.success(evaluationDirectory.absolutePath)
    }

    @Suppress("DEPRECATION")
    private fun getEvaluationDeviceInfo(result: MethodChannel.Result) {
        val currentActivity = activity
        if (currentActivity == null) {
            result.error("activity_missing", "Android activity is not attached.", null)
            return
        }

        try {
            val packageInfo = currentActivity.packageManager.getPackageInfo(
                currentActivity.packageName,
                0
            )
            val buildNumber = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                packageInfo.longVersionCode
            } else {
                packageInfo.versionCode.toLong()
            }
            result.success(
                mapOf(
                    "device_model" to Build.MODEL,
                    "android_version" to Build.VERSION.RELEASE,
                    "android_api_level" to Build.VERSION.SDK_INT,
                    "app_package_id" to currentActivity.packageName,
                    "app_version" to (packageInfo.versionName ?: "unknown"),
                    "build_number" to buildNumber.toString()
                )
            )
        } catch (error: PackageManager.NameNotFoundException) {
            result.error(
                "package_info_failed",
                "Could not read the installed app version.",
                error.toString()
            )
        }
    }

    private data class HandDetection(
        val values: List<Double>,
        val handedness: String,
        val averageX: Double
    )
}
