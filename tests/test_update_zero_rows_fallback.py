from app import app, db


def test_update_zero_rows_creates_new_save(client):
    # create a character
    resp = client.post('/stworz_postac', json={'imie':'ZeroTest','plec':'mezczyzna','lud':'polanie','klasa':'Wojownik','statystyki':{}})
    assert resp.status_code == 200

    with client.session_transaction() as sess:
        old_id = sess.get('postac_id')
        assert old_id is not None

    # delete the row from the DB to simulate mismatch
    db.usun_postac(old_id)

    # Call /zapisz_gre which should attempt to update and then create a new record when rows == 0
    resp2 = client.post('/zapisz_gre', json={})
    assert resp2.status_code == 200

    # Now check session postac_id has been refreshed
    with client.session_transaction() as sess:
        new_id = sess.get('postac_id')
        assert new_id is not None
        assert new_id != old_id

    # Check new save exists in DB
    loaded = db.wczytaj_postac(new_id)
    assert loaded is not None
    assert loaded['imie'] == 'ZeroTest'
