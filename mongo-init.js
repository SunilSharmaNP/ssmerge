// MongoDB initialization script for MERGE-BOT

// Create the application database
db = db.getSiblingDB('mergebot');

// Create collections with proper indexing
db.createCollection('users');
db.createCollection('mergeSettings'); 
db.createCollection('thumbnail');
db.createCollection('rcloneData');

// Create indexes for better performance
db.users.createIndex({ "_id": 1 }, { unique: true });
db.mergeSettings.createIndex({ "_id": 1 }, { unique: true });
db.thumbnail.createIndex({ "_id": 1 }, { unique: true });
db.rcloneData.createIndex({ "_id": 1 }, { unique: true });

// Create a sample user settings document (optional)
// db.mergeSettings.insertOne({
//   "_id": 123456789,
//   "name": "Sample User",
//   "user_settings": {
//     "merge_mode": 1,
//     "edit_metadata": false
//   },
//   "isAllowed": false,
//   "isBanned": false,
//   "thumbnail": null
// });

print("✅ MongoDB initialized successfully for MERGE-BOT");
