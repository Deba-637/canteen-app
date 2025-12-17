const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.resolve(__dirname, 'canteen.db');

const db = new sqlite3.Database(dbPath, (err) => {
    if (err) {
        console.error('Error opening database ' + dbPath + ': ' + err.message);
    } else {
        console.log('Connected to the SQLite database.');
        initDatabase();
    }
});

function initDatabase() {
    db.serialize(() => {
        // Create Students Table
        db.run(`CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll TEXT NOT NULL UNIQUE,
            dept TEXT NOT NULL
        )`);

        // Create Meals Table
        // Storing date as YYYY-MM-DD string
        db.run(`CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT NOT NULL,
            breakfast INTEGER DEFAULT 0,
            lunch INTEGER DEFAULT 0,
            dinner INTEGER DEFAULT 0,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )`);

        // Create Payments Table
        // Storing month as YYYY-MM string
        db.run(`CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            month TEXT NOT NULL,
            is_paid INTEGER DEFAULT 0,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )`);
        
        console.log('Database tables initialized.');
    });
}

module.exports = db;
