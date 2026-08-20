import sys
print(f"Python Location: {sys.executable}")

try:
    import tensorflow as tf
    print(f"✅ TensorFlow Version: {tf.__version__}")
    from tensorflow.keras.models import Sequential
    print("✅ Keras Import Success!")
except ImportError as e:
    print(f"❌ IMPORT ERROR: {e}")
except Exception as e:
    print(f"❌ OTHER ERROR: {e}")