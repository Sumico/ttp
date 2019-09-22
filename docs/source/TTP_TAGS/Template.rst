Template
========

TTP templates support <template> tag to define several templates within single template, each template processes separately, no data shared across templates.

Only two levels of hierarchy supported - top template tag and a number of child template tags within it, further template tags nested within children are ignored.

Use case of this functionality is to allow templates grouping under single definition and simplify loading - instead of adding each template to TTP object, all of the can be loaded in one go.

For instance::

    from ttp import ttp
    
    template1="""
    <group>
    interface {{ interface }}
     ip address {{ ip }}/{{ mask }}
    </group>
    """
    
    template2="""
    <group name="vrfs">
    VRF {{ vrf }}; default RD {{ rd }}
    <group name="interfaces">
      Interfaces: {{ _start_ }}
        {{ intf_list | ROW }} 
    </group>
    </group>
    """
    
    parser = ttp()
    parser.add_data(some_data)
    parser.add_template(template1)
    parser.add_template(template2)
    parser.parse()

Above code will produce same results as this code::

    from ttp import ttp
    
    template="""
    <template>
    <group>
    interface {{ interface }}
     ip address {{ ip }}/{{ mask }}
    </group>
    </template>
    
    <template>
    <group name="vrfs">
    VRF {{ vrf }}; default RD {{ rd }}
    <group name="interfaces">
      Interfaces: {{ _start_ }}
        {{ intf_list | ROW }} 
    </group>
    </group>
    </template>
    """
    
    parser = ttp()
    parser.add_data(some_data)
    parser.add_template(template)
    parser.parse()