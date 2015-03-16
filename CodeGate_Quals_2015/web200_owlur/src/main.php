<p>Welcome to owlur. The simple image sharing website for owl pictures.</p>
<p>Click <a href="index.php?page=view&id=random">here</a> to view a random owl.</p>
<img src="mainowl.jpg" style="width: 40%;">
<form action="index.php?page=upload" method="post" enctype="multipart/form-data">
    <p><b>Select owl image to upload:</b></p>
    <input type="file" name="fileToUpload" id="fileToUpload"><br>
    <input type="submit" value="Upload" name="submit">
</form>
