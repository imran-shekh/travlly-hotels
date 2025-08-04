window.onload = function ()
{
    document.getElementById( 'search-form' ).onsubmit = function ( e )
    {
        e.preventDefault();
        const cityInput = document.getElementById( 'city' );
        if ( !cityInput )
        {
            alert( "City input not found!" );
            return;
        }

        const city = cityInput.value.trim();
        if ( !city ) return;

        const resultsDiv = document.getElementById( 'results' );
        resultsDiv.innerHTML = "🔍 Searching hotels...";

        fetch( `/api/search_hotels?city=${ encodeURIComponent( city ) }` )
            .then( res => res.json() )
            .then( data =>
            {
                resultsDiv.innerHTML = "";
                if ( !data.hotels || data.hotels.length === 0 )
                {
                    resultsDiv.innerHTML = "❌ No hotels found.";
                    return;
                }

                data.hotels.forEach( hotel =>
                {
                    const div = document.createElement( "div" );
                    div.innerHTML = `
                        <strong>${ hotel.name }</strong><br/>
                        <small>${ hotel.address }</small><br/>
                        <em>${ hotel.roomType }</em><br/>
                        <span>💰 ${ hotel.price } ${ hotel.currency }</span><br/>
                        ${ hotel.image ? `<img src="${ hotel.image }" alt="Hotel Image" width="200"/><br/>` : "" }
                        <button onclick="selectHotel('${ hotel.id }','${ hotel.name.replace( /'/g, "\\'" ) }')">Book</button>
                    `;
                    resultsDiv.appendChild( div );
                } );
            } );
    };

    window.selectHotel = function ( id, name )
    {
        document.getElementById( 'booking-section' ).style.display = "block";
        document.getElementById( 'hotel_id' ).value = id;
        document.getElementById( 'booking-message' ).textContent = `Booking: ${ name }`;
    };

    document.getElementById( 'booking-form' ).onsubmit = function ( e )
    {
        e.preventDefault();
        const formData = new FormData( this );

        fetch( '/api/book_hotel', {
            method: 'POST',
            body: formData,
        } )
            .then( res => res.json() )
            .then( data =>
            {
                document.getElementById( 'booking-message' ).textContent = data.message;
            } );
    };
};
