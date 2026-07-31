# Ride-sharing-app

Mini project for the database course **COMP 232** (4th semester).

🔗 Live app: [eyatra.streamlit.app](https://eyatra.streamlit.app/)
🎥 Video demo: [youtu.be/byWhm-3wYsY](https://youtu.be/byWhm-3wYsY)

## Setup

```bash
git clone https://github.com/maheshpanta333/Ride-sharing-app.git
pip install -r requirements.txt
# but setup your own dbase with the .streamlit/secrets.toml file
streamlit run app.py
```

## Project Structure

- **`images/`** — UI screenshots of each module (admin, driver, complaints, tables, etc.), shown below.
- **`videos/`** — `RideSharingApp.mov`, a short screen-recording demo of the app in action (see embed below, or the YouTube link above).

## Screenshots

| | | |
|---|---|---|
| **Admin** <br> ![Admin](images/admin.png) | **Admin Table** <br> ![Admin Table](images/admintable.png) | **Driver** <br> ![Driver](images/driver.png) |
| **Driver Table** <br> ![Driver Table](images/driverstable.png) | **Complaint** <br> ![Complaint](images/complaint.png) | **Complaint Table** <br> ![Complaint Table](images/complainttable.png) |
| **Request Ride** <br> ![Request Ride](images/rqride.png) | **Trips Table** <br> ![Trips Table](images/tripstable.png) | **Users Table** <br> ![Users Table](images/userstable.png) |
| **Payment Table** <br> ![Payment Table](images/paymenttable.png) | **Vehicles Table** <br> ![Vehicles Table](images/vehiclestable.png) | |

## Demo Video

<video src="videos/RideSharingApp.mov" controls width="600">
  Your browser does not support embedded video. Watch the demo instead on
  <a href="https://youtu.be/byWhm-3wYsY">YouTube</a>.
</video>

> Note: GitHub's README renderer doesn't reliably play `.mov` files inline — if it doesn't show up, use the YouTube link above.
