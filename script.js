function createTable(domainName, tableName, tableData) {
    var table = document.createElement('table');
    table.classList.add('table');
    table.classList.add('table-striped');
    table.classList.add('table-bordered');
    table.classList.add('table-hover');

    var tableBody = document.createElement('tbody');
    var tableHead = document.createElement('thead');

    var headRow = true;
    tableData.forEach(function(rowData) {
        var row = document.createElement('tr');
        if(headRow) {
            row.classList.add('table-primary');
            
            rowData.forEach(function(cellData) {
                var cell = document.createElement('th');
                cell.appendChild(document.createTextNode(cellData));
                row.appendChild(cell);
            });

            tableHead.appendChild(row);

            headRow = false;
        }
        else {
            rowData.forEach(function(cellData) {
                var cell = document.createElement('td');
                cell.appendChild(document.createTextNode(cellData));
                row.appendChild(cell);
            });
            
            tableBody.appendChild(row);
        }
    });
        
    table.appendChild(tableHead);
    table.appendChild(tableBody);

    document.getElementById('data-container').appendChild(table);
}

function processResponse(data){
    console.log("Inside processResponse()", data);

    clearDataContainer(false); // This will clear the current spinner

    var no_records_found = true;

    for(key in data) {
        console.log('Domain Name = ' + key);
        for (itrTable in data[key]) {
            
            if( Array.isArray(data[key][itrTable]) ) {
                console.log('Table Name = ' + itrTable + ' :: isArray = ' + Array.isArray(data[key][itrTable]))
                createTable(key, itrTable, data[key][itrTable])
                no_records_found = false;
            }
            else {
                console.log('Key = ' + itrTable + ' :: value = ' + data[key][itrTable]);
            }
        }
    }

    if(no_records_found) {
        document.getElementById('data-container').appendChild(document.createTextNode('No Records found'));
    } else {
        document.getElementById('data-container').classList.add('mx-0');
    }
}

function startTrouble(env, key, value) {
    console.log('Entering into startTrouble');

    async function getData() {
        let response = await fetch('/t-rex/api/query?ENV=' + env + '&KEY=' + key + '&VALUE=' + value);
        let data = await response.json();
        return data;
    }

    getData().then( data => processResponse(data) );
}

function clearDataContainer(doSpinner) {
    // This is the fastest way to remove the child class rather than loop through them to delete
    // https://stackoverflow.com/questions/3955229/remove-all-child-elements-of-a-dom-node-in-javascript
    var dataContainer = document.getElementById("data-container");
    
    dataContainer.classList.remove('mx-0');

    if(doSpinner) {
        console.log('Adding spinner after clearing the container');
        dataContainer.innerHTML = '<div class="row">    <div class="col-md-8 offset-md-2">    <div id="id-spinner" class="lds-hourglass"></div>     </div>  </div>';
    } else {
        console.log('Clearing the container and not adding spinner');
        dataContainer.textContent = '';
    }
}

document.getElementById("id-submit").addEventListener("click", function(){
    console.log('Entered into submit form');

    var t_env = document.getElementById("id-env").value;
    console.log(t_env)

    var t_key = document.getElementById("id-key").value;
    console.log(t_key)

    var t_value = document.getElementById("id-value").value;
    console.log(t_value)

    if( t_value == '' ){
        document.getElementById("id-value").classList.add('is-invalid');
        return;
    }
    else {
        document.getElementById("id-value").classList.remove('is-invalid');
    }

    if(t_env === 'on') {
        t_env = 'SIT'
    } else {
        t_env = 'UAT'
    }
    
    clearDataContainer(true);
    startTrouble(t_env, t_key, t_value);

} );


//window.addEventListener("DOMContentLoaded", startTrouble, false);