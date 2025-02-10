from pyfingerprint.pyfingerprint import PyFingerprint
from pymongo import MongoClient
import time

# Initialize MongoDB client and database
client = MongoClient('localhost', 27017)
db = client['fingerprint_db']
collection = db['fingerprint_collection']

try:
    f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000) 
    #dev, the name of usb
    #ttyUSB0 name of the device file representing the USB-to-serial converter that the scanner is connected
    #57600 baud rate, the next is password and address
    
    if (f.verifyPassword() == False):
        raise ValueError('The given fingerprint sensor password is incorrect!')
except Exception as e:
    print('Error: ' + str(e))
    exit(1)

def register_fingerprint(fingerprint_id):
    fingerprint_data = {
        'fingerprint_id': fingerprint_id,
        'timestamp': time.time()
    }
    collection.insert_one(fingerprint_data)
    print('Fingerprint registered successfully!')

try:
    while True:
        # Wait for finger to be detected
        print('Waiting for finger...')
        while (f.readImage() == False):
            pass

         # Convert read image to characteristics
        f.convertImage(0x01)

        # Search for fingerprint in database
        result = f.searchTemplate()
        if result == -1:
            print('No matching fingerprint found.')
        else:
            print('Fingerprint already registered.')

        # Ask for confirmation to register fingerprint
        confirmation = input('Do you want to register this fingerprint? (yes/no): ').lower()
        if confirmation == 'yes':
            # Store fingerprint template
            position = f.storeTemplate()
            if position != -1:
                register_fingerprint(position)
            else:
                print('Error storing fingerprint.')
        else:
            print('Fingerprint not registered.')

except KeyboardInterrupt:
    print('Program interrupted by user.')
finally:
    client.close()
