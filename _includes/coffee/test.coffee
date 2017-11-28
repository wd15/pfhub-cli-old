assert = require('assert')


it('test mocha', ->
  assert.equal(1, 1)
)


it('test user_repo', ->
  assert.equal(user_repo('https://github.com/wd15/pymks/tree/master/doc'),
                         'wd15/pymks')
)


it('test to_date', ->
  assert.equal(to_date('Tue Jan 31 12:01:55 EST 2017'),
               'Jan 31, 2017')
)


it('test get_software', ->
  assert.equal(get_software('moose',
                            [{name:'MOOSE', value:0},
                             {name:'fipy', value:1}]).value,
               0)
)


it('test get_data', ->
  assert.equal(get_software('name1',
                            [{name:'name0', value:0},
                             {name:'name1', value:1}]).value,
               1)
)


it('test memory_usage', ->
  assert.equal(
    memory_usage(
      {data:[{name:'memory_usage', values:[{value:'1000', unit:'MB'}]},
             {name:'other', value:1}]}
    ),
   '1000.0 MB')
)


it('test count_uploads_num', ->
  data = ->
    {example:{},
    a:{meta:{benchmark:{id:'1a.0'}}},
    b:{meta:{benchmark:{id:'1a.0'}}},
    c:{meta:{benchmark:{id:'2a.0'}}}
    }

  assert.equal(count_uploads_num(1, data()), 2)
)


it('test count_uploads_id', ->
  data = ->
    {example:{},
    a:{meta:{benchmark:{id:'1a', version:1}}},
    b:{meta:{benchmark:{id:'1a', version:1}}},
    c:{meta:{benchmark:{id:'2a', version:1}}},
    d:{meta:{benchmark:{id:'1a', version:0}}}
    }
  assert.equal(count_uploads_id('1a.1', data()), 2)
)


benchmark_data_in = ->
  [
    {
      title:'first'
      revisions:
        [
          {
            variations:['a', 'b']
            version:1
          }
          {
            variations:['a', 'b']
            version:0
          }
        ]
    }
    {
      title:'second'
      revisions:
        [
          {
            version:1
            variations:['a', 'b']
          }
          {
            version:0
            variations:['a', 'b']
          }
        ]
    }
  ]


it('test get_columns', ->
  assert.equal(get_columns()[5].data, 'num')
)


it('test get_benchmark_data', ->
  assert.deepEqual(
    get_benchmark_data(benchmark_data_in()).data[0].title
    'first'
  )
)


describe('test flat_key', ->
  it('with a list', ->
    assert.deepEqual(
      flat_key('b', {a:0, b:[0, 1]})
      [{a:0, b:0}, {a:0, b:1}]
    )
  )
  it('with a dict', ->
    assert.deepEqual(
      flat_key('b', {a:0, b:[{c:0}, {c:1}]})
      [{a:0, b:{c:0}}, {a:0, b:{c:1}}]
    )
  )
)


describe('test flat_key_from_list', ->
  it('with one key', ->
    assert.deepEqual(
      flat_key_from_list('b', [{a:0, b:[1, 2]}, {a:3, b:[4, 5]}])
      [{a:0, b:1}, {a:0, b:2}, {a:3, b:4}, {a:3, b:5}]
    )
  )
)


describe('test transform_data', ->
  it('with test data', ->
    data_out = ->
      [
        {
          title:'first'
          variations:'a'
          revisions:
            {
              variations: ['a', 'b']
              version:1
            }
        }
        {
          title:'first'
          variations:'b'
          revisions:
            {
              variations: ['a', 'b']
              version:1
            }
        }
        {
          title:'first'
          variations:'a'
          revisions:
            {
              variations: ['a', 'b']
              version:0
            }
        }
        {
          title:'first'
          variations:'b'
          revisions:
            {
              variations: ['a', 'b']
              version:0
            }
        }
        {
          title:'second'
          variations:'a'
          revisions:
            {
              variations: ['a', 'b']
              version:1
            }
        }
        {
          title:'second'
          variations:'b'
          revisions:
            {
              variations: ['a', 'b']
              version:1
            }
        }
        {
          title:'second'
          variations:'a'
          revisions:
            {
              variations: ['a', 'b']
              version:0
            }
        }
        {
          title:'second'
          variations:'b'
          revisions:
            {
              variations: ['a', 'b']
              version:0
            }
        }
      ]
    assert.deepEqual(
      transform_data(benchmark_data_in())
      data_out()
    )
  )
)


describe('test benchmark_id', ->
  it('with sample data', ->
    data = ->
      {
        num:1
        variations:'a'
        revisions:{version:0, url:'http://wow.com'}
      }
    assert.deepEqual(
      benchmark_id({}, {}, data())
      '<a href="http://wow.com" target="_blank">\n1a.0\n</a>'
    )
  )
)


describe('test make_http', ->
  it('with no http', ->
    assert.deepEqual(make_http('wow').substr(0, 4), '/chi')
  )
  it('with http', ->
    assert.deepEqual(make_http('http://wow'), 'http://wow')
  )
)


describe('test commit', ->
  it('with test data', ->
    data_in = ->
      {revisions:{commit:{sha:'abcd', url:'a/b'}}}
    data_out = ->
      '<a href="https://github.com/usnistgov/chimad-phase-field/\
      blob/abcd/a/b" target="_blank">\nabcd\n</a>'
    assert.deepEqual(commit({}, {}, data_in()), data_out())
  )
)


describe('test filter_num_revision', ->
  data_in = ->
    {num:1, revisions:{version:1}}
  it('with true data', ->
    assert.deepEqual(filter_num_revision([1], 1)(data_in()), true)
  )
  it('with false data', ->
    assert.deepEqual(filter_num_revision([0], 1)(data_in()), false)
  )
  it('with null data', ->
    assert.deepEqual(filter_num_revision(null, null)(data_in()), true)
  )
)
