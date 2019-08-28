from .constants import *
from .property import *
from .validation import *
from .config import *
from rdflib import RDF
import logging
from logging.config import fileConfig


class SBOLObject:
    """An SBOLObject converts a Python data structure into an RDF triple store
     and contains methods for serializing and parsing RDF triples.
    """

    # 'Protected' members
    _namespaces = None
    _default_namespace = None
    _hidden_properties = None

    # def _init(self, rdf_type, uri):
    #     raise NotImplementedError("Not yet implemented")

    def _serialize(self):
        # Convert and SBOL object into RDF triples.
        raise NotImplementedError("Not yet implemented")

    def _nest(self):
        # Pretty-writer that converts flat RDF/XML into nested RDF/XML (ie. SBOL)
        raise NotImplementedError("Not yet implemented")

    def _makeQName(self, uri):
        raise NotImplementedError("Not yet implemented")

    def _register_extension_class(self, ns, ns_prefix, class_name):
        """Register an extension class and its namespace, so custom data can be embedded into and read from SBOL files.

        :param ns: The extension namespace, eg, http://myhome.org/my_extension#.
        It's important that the namespace ends in a forward-slash or hash.
        :param ns_prefix: A shorthand symbol for the full namespace as it will appear in the output file,
        eg. my_extension.
        :param class_name: The extension class name.
        :return: The new class.
        """
        raise NotImplementedError("Not yet implemented")

    # 'Public' members
    doc = None
    rdf_type = None
    parent = None
    properties = None
    owned_objects = None

    # TODO Docstrings on variables isn't a thing in Python. Consider using Epydoc.
    # The identity property is REQUIRED by all Identified objects and has a data type of URI.
    # A given Identified object's identity URI MUST be globally unique among all other identity URIs.
    # The identity of a compliant SBOL object MUST begin with a URI prefix that maps to a domain
    # over which the user has control. Namely, the user can guarantee uniqueness of identities within this domain.
    # For other best practices regarding URIs see Section 11.2 of the
    # [SBOL specification document](http://sbolstandard.org/wp-content/uploads/2015/08/SBOLv2.0.1.pdf).
    _identity = None

    def __init__(self, _rdf_type=URIRef(UNDEFINED), uri=URIRef("example")):
        """Open-world constructor."""
        if os.path.exists(LOGGING_CONFIG):
            fileConfig(LOGGING_CONFIG)
        self.logger = logging.getLogger(__name__)
        if not os.path.exists(LOGGING_CONFIG):
            self.logger.setLevel(logging.INFO)
        self.owned_objects = {}  # map<rdf_type, vector<SBOLObject>>
        self.properties = {}  # map<rdf_type, vector<SBOLObject>>
        if type(_rdf_type) is str:
            self.rdf_type = URIRef(_rdf_type)
        else:
            self.rdf_type = _rdf_type
        self._namespaces = {}
        if not isinstance(uri, URIRef):
            self.logger.debug("Property was not a URIRef: '" + str(uri) + "', " + str(type(uri)))
            self._identity = URIProperty(self, SBOL_IDENTITY, '0', '1', [sbol_rule_10202], URIRef(uri))
        else:
            self._identity = URIProperty(self, SBOL_IDENTITY, '0', '1', [sbol_rule_10202], uri)
        if hasHomespace():
            uri = os.path.join(getHomespace(), uri)
            self._identity = URIProperty(self, SBOL_IDENTITY, '0', '1', [sbol_rule_10202], uri)

    @property
    def identity(self):
        # Return the value associated with the identity property
        return self._identity.value

    @identity.setter
    def identity(self, new_identity):
        self._identity.value = new_identity

    def getTypeURI(self):
        """
        :return: The uniform resource identifier that describes the RDF-type of this SBOL Object.
        """
        return self.rdf_type

    def getClassName(self, rdf_type):
        """Parses a local class name from the RDF-type of this SBOL Object."""
        if '#' in rdf_type:
            return rdf_type.split('#')[1]
        else:
            return rdf_type

    def find(self, uri):
        """Search this object recursively to see if an object or any child object with URI already exists.

        :param uri: The URI to search for.
        :return: The SBOLObject associated with this URI if it exists, None otherwise.
        """
        if self.identity == uri:
            return self
        for rdf_type, object_store in self.owned_objects.items():
            if rdf_type in self._hidden_properties:
                continue
            for obj in object_store:
                match = obj.find(uri)
                if match is not None:  # NOTE: original implementation has 2 recursive calls, which is probably bad...
                    return match
        return None

    def cacheObjects(self, objectCache):
        """TODO document

        :param objectCache: a dictionary mapping strings to SBOLObjects
        :return: None
        """
        raise NotImplementedError("Not yet implemented")

    def find_property(self, uri):
        """Search this object recursively to see if it contains a member property with the given RDF type.

        :param uri: The RDF type of the property to search for.
        :return: The SBOLObject that contains a member property with the specified RDF type, None otherwise
        """
        if uri in self.owned_objects and uri in self.properties:
            return self
        for rdf_type, object_store in self.owned_objects.items():
            for obj in object_store:
                match = obj.find_property(uri)
                if match:
                    return match
        return None

    def find_property_value(self, uri, value, matches=None):
        """Search this object recursively to see if it contains a member property with the given RDF type
        and indicated property value.

        :param uri: The RDF type of the property to search for.
        :param value: The property value to match.
        :param matches:
        :return: A vector containing all objects found that contain a member property with the specified RDF type
        """
        matches = []
        for rdf_type, store in self.owned_objects.items():
            # Skip hidden and aliased properties
            if rdf_type in self._hidden_properties:
                continue
            for obj in store:
                matches += obj.find_property_value(uri, value)
        value_store = self.properties[uri]
        for val in value_store:
            matches.append(val)
        return matches

    def find_reference(self, uri):
        """Search this object recursively to see if it contains a member property with the given RDF type
        and indicated property value.

        :param uri: A URI, either an ontology term or an object reference, to search for.
        :return: A vector containing all objects found that contain the URI in a property value.
        """
        raise NotImplementedError("Not yet implemented")

    def compare(self, comparand):
        """Compare two SBOL objects or Documents. The behavior is currently undefined for objects
        with custom annotations or extension classes.

        :param comparand: The object being compared to this one.
        :return: True if the objects are identical, False if they are different.
        """
        # TODO This may work differently than the original method...
        if type(comparand) != type(self):
            self.logger.warning("TYPES ARE NOT EQUAL!!!")
            return False
        is_equal = True
        if self.rdf_type != comparand.rdf_type:
            self.logger.warning(self.identity + ' does not match type of ' + comparand.rdf_type)
            return False
        if self.rdf_type == SBOL_DOCUMENT:
            ns_set = set(())
            comparand_ns_set = set(())
            for val in self._namespaces.values():
                ns_set.add(val)
            for val in comparand._namespaces.values():
                comparand_ns_set.add(val)
            if ns_set != comparand_ns_set:
                self.logger.warning("NAMESPACES ARE NOT EQUAL!!!")
                is_equal = False
        self.logger.debug("Here are my properties: " + str(self.properties))
        self.logger.debug("Here are their properties: " + str(comparand.properties))
        if self.compare_unordered_lists(self.properties, comparand.properties) is False:
            self.logger.warning("PROPERTIES ARE NOT EQUAL!!!")
            is_equal = False
        self.logger.debug("Here are my owned objects: " + str(self.owned_objects))
        self.logger.debug("Here are their owned objects: " + str(comparand.owned_objects))
        if self.compare_unordered_lists(self.owned_objects, comparand.owned_objects) is False:
            self.logger.warning("OWNED OBJECTS ARE NOT EQUAL!!!")
            is_equal = False
        return is_equal

    def compare_unordered_lists(self, mine, theirs):
        """This is a very inefficient hack for comparing two unordered mutable lists.

        We could make some small improvements to this approach, or consider alternatives."""
        for my_obj in mine:
            found = False
            for their_obj in theirs:
                if my_obj == their_obj:
                    found = True
                    break
            if found is False:
                return False
        return True

    def __eq__(self, other):
        """Compare two SBOL objects or Documents. The behavior is currently undefined for objects
        with custom annotations or extension classes.

        :param other: The object being compared to this one.
        :return: True if the objects are identical, False if they are different.
        """
        # if other is None or not isinstance(other, SBOLObject):
        #     return False
        # if self.rdf_type != other.rdf_type:
        #     print(self.identity.get() + ' does not match type of ' + other.type())
        return self.compare(other)

    def getPropertyValue(self, property_uri):
        """Get the value of a custom annotation property by its URI.

        :param property_uri: The URI for the property.
        :return: The value of the property or SBOL_ERROR_NOT_FOUND.
        """
        raise NotImplementedError("Not yet implemented")

    def getPropertyValues(self, property_uri):
        """Get all values of a custom annotation property by its URI.

        :param property_uri: The URI for the property.
        :return: A vector of property values or SBOL_ERROR_NOT_FOUND.
        """
        raise NotImplementedError("Not yet implemented")

    def getProperties(self):
        """Gets URIs for all properties contained by this object. This includes SBOL core properties as well as
        custom annotations. Use this to find custom extension data in an SBOL file.

        :return: A vector of URIs that identify the properties contained in this object.
        """
        property_uris = [p for p in self.properties.keys()]
        owned_objects_uris = [p for p in self.owned_objects.keys()]
        return property_uris + owned_objects_uris

    def setPropertyValue(self, property_uri, val):
        """Set and overwrite the value for a user-defined annotation property.

        :param property_uri:
        :param val: Either a literal or URI value.
        :return: None
        """
        raise NotImplementedError("Not yet implemented")

    def addPropertyValue(self, property_uri, val):
        """Append a value to a user-defined annotation property.

        :param property_uri:
        :param val: Either a literal or URI value.
        :return: None
        """
        raise NotImplementedError("Not yet implemented")

    def setAnnotation(self, property_uri, val):
        """Set the value for a user-defined annotation property. Synonymous with setPropertyValue.

        :param property_uri:
        :param val: If the value is a URI, it should be surrounded by angle brackets,
        else it will be interpreted as a literal value.
        :return: None
        """
        raise NotImplementedError("Not yet implemented")

    def getAnnotation(self, property_uri):
        """Get the value of a custom annotation property by its URI. Synonymous with getPropertyValue.

        :param property_uri: The URI for the property.
        :return: The value of the property or SBOL_ERROR_NOT_FOUND.
        """
        raise NotImplementedError("Not yet implemented")

    def apply(self, callback, user_data):
        """
        TODO document
        :param callback:
        :param user_data:
        :return: None
        """
        raise NotImplementedError("Not yet implemented")

    def update_uri(self):
        """
        Recursively generates SBOL compliant ids for an object and all
        its owned objects, then checks to make sure that these ids are unique.
        :return: None
        """
        raise NotImplementedError("Implemented by child classes")

    def build_graph(self, graph):
        graph.add((self._identity.getRawValue(), RDF.type, self.rdf_type))
        for typeURI, proplist in self.properties.items():
            for prop in proplist:
                graph.add((self._identity.getRawValue(), typeURI, prop))
        for typeURI, objlist in self.owned_objects.items():
            for owned_obj in objlist:
                graph.add((self._identity.getRawValue(), typeURI, owned_obj.identity))
                owned_obj.build_graph(graph)

    def serialize_rdf2xml(self, graph):
        """Serialize the SBOLObject.

        :param os: Output stream.
        :param indentLevel:
        :return: None
        """
        # Serialize properties
        for rdf_type, vals in self.properties.items():
            if rdf_type == 'http://sbols.org/v2#identity':
                # This property is not serialized
                continue
            #if len(vals) == 1 and (vals[0] == '""' or vals[0] == '<>'):
            if len(vals) == 0:
                #  No properties of this type
                continue
            predicate = self.doc.referenceNamespace(rdf_type)
            for val in vals:
                graph.add((self._identity.getRawValue(), predicate, val))
        # Serialize owned objects
        for name, object_store in self.owned_objects:
            if len(object_store) == 0:
                continue
            # predicate = self.doc.referenceNamespace(name)
            for obj in object_store:
                # NOTE: couldn't we just use 'name'? (Would probably work the same, but wanted
                # to follow the original implementation as closely as possible.)
                typeURI = obj.getTypeURI()
                if typeURI in self._hidden_properties:
                    continue
                rdfType = self.doc.referenceNamespace(typeURI)
                graph.add((self._identity.getRawValue(), rdfType, obj.identity))
                obj.serialize_rdf2xml(graph) # recursive

    def __str__(self):
        return self.identity  # identity should be a URIRef``

    def is_top_level(self):
        return False
